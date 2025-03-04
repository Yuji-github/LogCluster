#!/bin/bash

mkdir -p logs
cd logs || exit
wget https://zenodo.org/record/3227177/files/Android.tar.gz && tar -xvzf Android.tar.gz && rm -rf Android.tar.gz
wget https://zenodo.org/record/3227177/files/Apache.tar.gz && tar -xvzf Apache.tar.gz && rm -rf Apache.tar.gz
wget https://zenodo.org/record/3227177/files/BGL.tar.gz && tar -xvzf BGL.tar.gz && rm -rf BGL.tar.gz
wget https://zenodo.org/record/3227177/files/Hadoop.tar.gz && tar -xvzf Hadoop.tar.gz && rm -rf Hadoop.tar.gz
wget https://zenodo.org/record/3227177/files/HDFS_1.tar.gz && tar -xvzf HDFS_1.tar.gz && rm -rf HDFS_1.tar.gz
wget https://zenodo.org/record/3227177/files/HealthApp.tar.gz && tar -xvzf HealthApp.tar.gz && rm -rf HealthApp.tar.gz
wget https://zenodo.org/record/3227177/files/HPC.tar.gz && tar -xvzf HPC.tar.gz && rm -rf HPC.tar.gz
wget https://zenodo.org/record/3227177/files/Linux.tar.gz && tar -xvzf Linux.tar.gz && rm -rf Linux.tar.gz
wget https://zenodo.org/record/3227177/files/Mac.tar.gz && tar -xvzf Mac.tar.gz && rm -rf Mac.tar.gz
wget https://zenodo.org/record/3227177/files/Proxifier.tar.gz && tar -xvzf Proxifier.tar.gz && rm -rf Proxifier.tar.gz
wget https://zenodo.org/record/3227177/files/SSH.tar.gz && tar -xvzf SSH.tar.gz && rm -rf SSH.tar.gz
wget https://zenodo.org/record/3227177/files/Thunderbird.tar.gz && tar -xvzf Thunderbird.tar.gz && rm -rf Thunderbird.tar.gz
wget https://zenodo.org/record/3227177/files/Windows.tar.gz && tar -xvzf Windows.tar.gz && rm -rf Windows.tar.gz
wget https://zenodo.org/record/3227177/files/Zookeeper.tar.gz && tar -xvzf Zookeeper.tar.gz && rm -rf Zookeeper.tar.gz