#!/bin/bash

#Build ctp/lts/ib api

echo "�Ƿ�Ҫ��װ'CTP'�ӿ�? (Do you need 'CTP' interface?)"
read -p "Enter [y]n: " var1
var1=${var1:-y}
if [ "$var1" = "y" ]; then
	pushd vnpy/api/ctp
	bash build.sh
	popd
fi

echo "�Ƿ�Ҫ��װ'LTS'�ӿ�? (Do you need 'LTS' interface?)"
read -p "Enter [y]n: " var1
var1=${var1:-y}
if [ "$var1" = "y" ]; then
	pushd vnpy/api/lts
	bash build.sh
	popd
fi

echo "�Ƿ�Ҫ��װ'XTP'�ӿ�? (Do you need 'XTP' interface?)"
read -p "Enter [y]n: " var1
var1=${var1:-y}
if [ "$var1" = "y" ]; then
	pushd vnpy/api/xtp
	bash build.sh
	popd
fi

echo "�Ƿ�Ҫ��װ'IB'�ӿ�? (Do you need 'IB' interface?)"
read -p "Enter [y]n: " var1
var1=${var1:-y}
if [ "$var1" = "y" ]; then
	pushd vnpy/api/ib
	bash build.sh
	popd
fi

#Install Python Modules
pip install -r requirements.txt

#Install Ta-Lib
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --set show_channel_urls yes
conda install -c quantopian ta-lib=0.4.9

#Install vn.py
python setup.py install

