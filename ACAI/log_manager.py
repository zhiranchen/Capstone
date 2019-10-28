import copy
from utils import Node


class LogManager:
    def __init__(self):
        self.separator = "\t#\t"
        
        # Key: <str> NodeName + "\t#\t" + FileSetVersion
        # val: [(InputNodeName, FileSetVersion)]
        self.reverse_log = {}

        # key: <str> NodeName + "\t#\t" + FileSetVersion
        # val: <dict> hyper_parameter
        self.fileset_hp = {}

        # key: <str> Node_name + "\t#\t" + ScriptVersion + "\t#\t" + Inputs
        # value: (hyper_parameter(dict), OutputFileSetVersion)
        self.log = {}

        
    def convert_inputs_to_str(self, inputs):
        convert_str = ""
        for one_tuple in sorted(inputs):
            input_node_name = one_tuple[0]
            fileset_version = one_tuple[1]
            convert_str += str(input_node_name) + self.separator + str(fileset_version) + self.separator
        convert_str = convert_str[0: len(convert_str)-len(self.separator)]
        return convert_str


    def generate_node_key(self, node_name, script_version, inputs):
        return str(node_name) + self.separator + str(script_version) + self.separator + self.convert_inputs_to_str(inputs)


    def dfs_visit(self, node_name, fileset_version, cur_path, paths):
        tmp_key = node_name + self.separator + str(fileset_version)
        
        if tmp_key not in self.reverse_log:
            paths.append(copy.deepcopy(cur_path))
            return
        
        inputs = self.reverse_log[tmp_key]

        for one_tuple in inputs:
            input_node = one_tuple[0]
            input_fs_version = one_tuple[1]

            new_path = copy.deepcopy(cur_path)
            new_path[input_node] = input_fs_version
            # new_path.add(input_node)
            self.dfs_visit(input_node, input_fs_version, new_path, paths)


    def tracking_ancestors(self, inputs):
        all_paths = []
        
        for one_tuple in inputs:
            input_node = one_tuple[0]
            input_fs_version = one_tuple[1]

            cur_path = {input_node: input_fs_version}
            self.dfs_visit(input_node, input_fs_version, cur_path, all_paths)

        return all_paths


    # return true if valid
    # return false is there is invalid ancestors
    def check_ancestors_hp(self, paths):
        for i in range(0, len(paths)):
            for j in range(i+1, len(paths)):
                path1 = paths[i]
                path2 = paths[j]

                for one_node in path1:
                    if one_node in path2:
                        fs_version1 = path1[one_node]
                        fs_version2 = path2[one_node]

                        if fs_version1 == fs_version2:
                            continue

                        # if different file_version
                        # check if hp has the same value
                        hp1 = self.fileset_hp[one_node + self.separator + str(fs_version1)]
                        hp2 = self.fileset_hp[one_node + self.separator + str(fs_version2)]

                        if len(hp1) != len(hp2):
                            return False

                        for one_hp in hp1:
                            if hp1[one_hp] != hp2[one_hp]:
                                return False
        
        return True


    def ExperimentRun(self, node_name, script_version, hyper_parameter, inputs):
        check_log = self.generate_node_key(node_name, script_version, inputs)
        
        if check_log in self.log:
            all_match = True
            hp_dict = self.log[check_log][0]

            for one_hp in hyper_parameter:
                if one_hp not in hp_dict:
                    all_match = False
                    break

                if hp_dict[one_hp] != hyper_parameter[one_hp]:
                    all_match = False
                    break
            
            if all_match:
                return False

        all_paths = self.tracking_ancestors(inputs)
        return self.check_ancestors_hp(all_paths)


    def SaveOutputData(self, node_name, script_version, hyper_parameter, inputs, output_fileset_version):
        log_key = self.generate_node_key(node_name, script_version, inputs)
        self.log[log_key] = (hyper_parameter, output_fileset_version)
        
        reverse_log_key = node_name + self.separator + str(output_fileset_version)
        self.reverse_log[reverse_log_key] = inputs
        self.fileset_hp[reverse_log_key] = hyper_parameter


# for testing
if __name__ == "__main__":
    lm = LogManager()
    
    # inputs = [("b.py", 1), ("a.py", 2), ("c.py", 3)]
    # # print(lm.convert_inputs_to_str(inputs))

    # hp_test = {'x1': 1.2, 'x2': 0.5}
    # lm.SaveOutputData("e.py", 2, hp_test, inputs, 2)

    # for key in lm.log:
    #     print(key)
    #     print(lm.log[key])

    lm.reverse_log["b" + lm.separator + "1"] = [("a", 1)]
    lm.reverse_log["d" + lm.separator + "1"] = [("b", 1), ("c", 3)]
    
    lm.reverse_log["g" + lm.separator + "2"] = [("e", 2), ("f", 1)]
    lm.reverse_log["e" + lm.separator + "2"] = [("h", 1)]
    lm.reverse_log["f" + lm.separator + "1"] = [("h", 1)]

    lm.reverse_log["g" + lm.separator + "1"] = [("e", 1), ("f", 2)]
    lm.reverse_log["e" + lm.separator + "1"] = [("h", 2)]
    lm.reverse_log["f" + lm.separator + "2"] = [("h", 2)]

    inputs = [("d", 1), ("g", 1)]

    print(lm.tracking_ancestors(inputs))