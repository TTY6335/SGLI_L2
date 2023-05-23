# This Program?    
JAXA GCOM-C SGLIのLevel2のHDF5ファイルをgeotiffに変換とESRI:53008に投影変換するpythonプログラムです。
GCOM-C タイルデータそのままをGeotiffにして出力します。  
G-Portalで加工要求して作成したGeotiffファイルと同じ投影方法になっています。  
ただし、Nodataに入っている値については異なっています。  
ESRI:53008上での位置の計算には [しきさいポータルの計算方法](https://shikisai.jaxa.jp/faq/faq0062_j.html) を使用しています。
h5pyを使用せずにgdalライブラリでファイル読み込み、処理が完結するようになっています。  
使い方等はWikiを読んでください。

This is a Python program for converting JAXA GCOM-C SGLI Level 2 HDF5 files to GeoTIFF format and performing projection transformation to ESRI:53008.
It directly converts GCOM-C tile data to GeoTIFF format, maintaining the same projection as the Geotiff files created by processing requests on G-Portal. However, the handling of values that are marked as Nodata may differ.
The program uses the calculation method described in the [Shikisai Portal](https://shikisai.jaxa.jp/faq/faq0062_j.html) to calculate the positions on the ESRI:53008 projection.
It uses the gdal library for file reading and processing, without relying on h5py. Please refer to the Wiki for usage instructions and more details.


# Environment  
 開発環境は以下です。
* CentOS Linux release 7.7.1908 (Core)
* python 3.7.4
* ~h5py 2.9.0~
* hdf5 1.10.4
* numpy 1.16.5
* gdal 3.2.0dev
