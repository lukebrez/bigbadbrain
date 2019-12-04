#!/bin/bash
#SBATCH --job-name=cmtk
#SBATCH --partition=trc
#SBATCH --time=1:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --output=./output/slurm-%j.out

echo $PWD
cd /oak/stanford/groups/trc/data/Brezovec/2P_Imaging/20190101_walking_dataset/20191204_anatomy_collection/
echo $PWD



master=Template.nii
slave="$1"
echo "slave"
echo $slave
munger -a -w -X 26 -C 8 -G 80 -R 4 -A '--accuracy 0.4' -W '--accuracy 0.4' -T 4 -s $master $slave
cmtk reformatx -o ./warped/${master}_warped.nii --floating Template.nii Meanbrain.nii Registration/warp/Meanbrain_Template.nii_warp_m0g80c8e1e-1x26r4.list/