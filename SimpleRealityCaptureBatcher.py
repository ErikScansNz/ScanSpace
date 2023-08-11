# A very simple reality capture batcher
# Takes a root folder input with one folder per scan to process
# Each scan folder must contain an /images/ subfolder containing the scan images
# each scan is saved into the scan folder using the
# Written by Erik Christensen, 2023

import os
import subprocess
from multiprocessing import Process, Queue, freeze_support

# Path to RealityCapture.exe, change this to your own path.
# this assumes you have the Reality Capture executable in the PATH environment variable
# you can change it to the exact path if you want
realityCapture = "RealityCapture.exe"

def run_rc(input_folder, done_queue):
    # Iterating through datasets from the task queue
    for data in iter(input_folder.get, 'STOP'):
        # Extracting dataset information and constructing paths
        dataset = data[0]
        directory = data[1]
        datasetPath = os.path.join(directory, dataset)
        image_path = os.path.join(datasetPath + "\\" + "images")
        output_path = os.path.join(directory + "\\" + dataset + "\\scanFiles")
        rc_output = os.path.join(output_path + "\\" + f"{dataset}.rcproj")
        geometry_output_path = os.path.join(datasetPath + "\\" + "geometry")

        try:
            # Check and create output_path if it doesn't exist
            if not os.path.exists(output_path):
                print("outputPath does not exist, creating it...")
                os.makedirs(output_path)

            # Check and create geometry_output_path if it doesn't exist
            if not os.path.exists(geometry_output_path):
                print("geometry_output_path does not exist, creating it...")
                os.makedirs(geometry_output_path)

            # Constructing RealityCapture command
            cmd = (f" -addFolder {image_path} -align -selectMaximalComponent "
                    f"-setReconstructionRegionAuto -scaleReconstructionRegion 1.3 1.3 1.7 center factor "
                    f"-calculateNormalModel -renameSelectedModel rawMesh "
                    f"-simplify 1000000 -renameSelectedModel mesh1m -calculateTexture "
                    f"-simplify 100000 -renameSelectedModel mesh100k "
                    f"-selectModel mesh1m -exportSelectedModel {geometry_output_path}\\{dataset}_mesh1m.obj "
                    f"-selectModel mesh100k -exportSelectedModel {geometry_output_path}\\{dataset}_mesh100k.obj")
            # Running RealityCapture command
            subprocess.run(f"{realityCapture} -setInstanceName rc1 {cmd} -save {rc_output} -clearCache -quit", shell=True)
            # Sending result to done queue
            done_queue.put([dataset, rc_output])
        except Exception as e:
            print(e)
            pass

def worker_task(directory):
    # Listing folders in the given directory
    folder_list = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
    task_queue = Queue()
    done_queue = Queue()

    # Filling task queue with datasets and directory information
    for dataset in folder_list:
        data = [dataset, directory]
        task_queue.put(data)

    print('task_queue size: ' + str(task_queue.qsize()))

    # Starting processing function in a separate process
    Process(target=run_rc, args=(task_queue, done_queue)).start()

    # Receiving and printing results
    for i in range(len(folder_list)):
        print('output: \t', done_queue.get())

    # Sending stop signal to task queue
    for i in range(len(folder_list)):
        task_queue.put('STOP')

if __name__ == '__main__':
    # Prompting user for directory path until a valid path is entered
    directory = input("Enter the directory path: ")
    while not os.path.isdir(directory):
        print("Invalid path, please enter a valid directory path.")
        directory = input("Enter the directory path: ")
    # Necessary for Windows multiprocessing
    freeze_support()
    # Starting main worker task
    worker_task(directory)
