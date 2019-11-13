from shutil import copyfile
import os
import pickle
import sys
import shutil
import collections
import subprocess

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

class Mock(object):
    def __init__(self, user_workspace, mock_workspace):
        self.user_dir = user_workspace
        self.mock_dir = mock_workspace
        self.filesets = {} # {fileset_name: [file_paths,...]}
        self.job_versions = collections.defaultdict(int) # {node_name: highest_version_executed_so_far + 1}
        self.history_path = os.path.join(self.mock_dir, "record.pkl")
        try:
            self.filesets, self.job_versions = pickle.load(open(self.history_path, "rb"))
        except:
            print("initiated with no history")

    def persist_to_disk(self):
        record = (self.filesets, self.job_versions)
        pickle.dump(record, open(self.history_path, "wb"))

    # return list of all file paths in dir 
    # path: relative path to workspace
    # returned path is relative path to workspace
    def list_all_file_paths(self, path):
        # if dir is a file itself, return [dir]
        path = os.path.join(self.mock_dir, path)
        if os.path.isfile(path):
            return [path]
        all_rel_paths = []
        for r, d, f in os.walk(path):
            for file in f:
                all_rel_paths.append(os.path.relpath(os.path.join(r, file), start=self.mock_dir))
        return all_rel_paths


    # create job folder with the name of job_name
    # transfer all files needed and the script and the files in filesets into the job folder
    # create a new process and run the job folder
    # return output fileset:V
    def run_job(self, script, filesets, files, job_name, command):
        # create job folder, update job_versions dict
        job_version = self.job_versions[job_name]
        self.job_versions[job_name] += 1
        job_name_V = job_name + ":" + str(job_version)
        job_folder_path = os.path.join(self.mock_dir, job_name_V)
        os.mkdir(job_folder_path)

        # add all needed file abs/rel paths into needed_filepaths
        needed_file_abs_paths = []
        needed_file_rel_paths = []
        for file in files + [script]:
            needed_file_rel_paths.append(file)
            needed_file_abs_paths.append(os.path.join(self.user_dir, file))
        for fileset in filesets:
            for relpath in self.list_all_file_paths(fileset):
                needed_file_rel_paths.append(relpath)
                needed_file_abs_paths.append(os.path.join(self.mock_dir, relpath))

        # copy all needed files into job folder
        for abspath, relpath in zip(needed_file_abs_paths, needed_file_rel_paths):
            source_path = abspath
            target_path = os.path.join(job_folder_path, relpath)
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            shutil.copy2(source_path, target_path)

        # TODO: create new process and then run script
        # pid=os.fork()
        # if pid:
        #     # parent
        #     return job_name_V  
        # else:
        #     # child
        #     os.chdir(job_folder_path)
        #     exec(open(script).read())
        #     for file in needed_file_rel_paths:
        #         os.remove(file)
        #     sys.exit()

        # execute script
        # no multi-process version
        
        # with cd(job_folder_path):
        #     exec(open(script).read())
        #     for file in needed_file_rel_paths:
        #         os.remove(file)
        
        process = subprocess.Popen(command.split(), cwd=job_folder_path, stdout=subprocess.PIPE)
        output, error = process.communicate()


        return job_name_V
