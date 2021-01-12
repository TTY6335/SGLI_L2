# coding:utf-8
import numpy as np
import gdal,sys
import gdalconst

__author__ = "TTY6335 https://github.com/TTY6335"

#タイル番号、画素の位置に対応する緯度経度のメッシュを返す関数
#4800x4800ピクセルすべての緯度経度を求めても遅い＆gdal_translateでエラーになるので間引き
#四隅が欲しいのでgcpの配列の大きさは縦横+1してある
def get_L2_geomesh(filename,lintile,coltile):

	#グラニュールIDからタイル番号を取得する
	#縦方向
	vtile=int(filename[21:23])
	#横方向
	htile=int(filename[23:25])
   
	#SGLI/L2であれば固定
	#縦方向の総タイル数
	vtilenum=18
	#横方向の総タイル数
	htilenum=36
		
	#緯度方向(dlin)、経度方向(dcol)
	#それぞれの1画素の大きさ
	#d=dlin=dcol
	d=180.0/lintile/vtilenum
		
	#求めたりタイル番号の左上画素の中心の緯度[deg]は、
	#1タイルあたりの角度が10[deg]であることから、
	lat0=90.0-vtile*10-d/2

	#求めたいタイル番号の左上画素の中心の経度[deg]は、
	#1タイルあたりの角度が10[deg]であることから、
	lon0=-180.0+htile*10+d/2

	#gdal_translateに与えるGCPのリスト
	gcp_list=[]

	for lin in range(0,lintile+1,100):
		lat=lat0-lin*d
		y=6371007.181*np.radians(lat)
		r=np.cos(np.radians(lat))
		for col in range(0,coltile+1,100):
			if(lin==lintile):
				lin=lin-1
			if(col==coltile):
				col=col-1
			lon=(lon0+col*d)/r
			x=6371007.181*r*np.radians(lon)
			gcp=gdal.GCP(x,y,0,col+0.5,lin+0.5)
			gcp_list.append(gcp)

	return gcp_list
 

if __name__ == '__main__':

#入力するファイルの情報#
	#ファイル名
	input_file=sys.argv[1]
	#バンド名
	band_name=sys.argv[2]

#出力ファイル名
	output_file=sys.argv[3]

	try:
		hdf_file = gdal.Open(input_file, gdal.GA_ReadOnly)
	except:
		print('%s IS MISSING.' % input_file)
		exit(1);
	
	hdf_file = gdal.Open(input_file, gdal.GA_ReadOnly)
	dataset_list=hdf_file.GetSubDatasets()

	print('OPEN %s.' % input_file)
	## Open HDF file

	# Open raster layer
	#プロダクト名を探す
	product_name='//Image_data/'+band_name
	for dataset_index in range(len(dataset_list)):
		if('//Geometry_data/Latitude' in dataset_list[dataset_index][0]):
			lat_index=dataset_index
		if('//Geometry_data/Longitude' in dataset_list[dataset_index][0]):
			lon_index=dataset_index
		if(product_name in dataset_list[dataset_index][0]):
			break;

	if not (product_name in dataset_list[dataset_index][0]):
		print('%s IS MISSING.' % band_name)
		print('SELECT FROM')
		for dataset in dataset_list:
			if('Image_data' in dataset[0]):
				print(dataset[0].split('/')[-1])
		exit(1);


	Image_var=gdal.Open(hdf_file.GetSubDatasets()[dataset_index][0], gdal.GA_ReadOnly).ReadAsArray()

	#Get Sole, Offset,Minimum_valid_DN, Maximum_valid_DN
	Metadata=hdf_file.GetMetadata_Dict()
	hdf_filename=Metadata['Global_attributes_Product_file_name']

	for metadata_lavel in Metadata.keys():
		if band_name+'_Slope' in metadata_lavel:
			Slope=float(Metadata[metadata_lavel])
		if band_name+'_Offset' in metadata_lavel:
			Offset=float(Metadata[metadata_lavel])
		if band_name+'_Minimum_valid_DN' in metadata_lavel:
			Minimum_valid_DN=float(Metadata[metadata_lavel])
		if band_name+'_Maximum_valid_DN' in metadata_lavel:
			Maximum_valid_DN=float(Metadata[metadata_lavel])
		if band_name+'_Data_description' in metadata_lavel:
			Data_description=Metadata[metadata_lavel]
	#型変換とエラー値をnanに変換する
	Image_var=np.array(Image_var,dtype='uint16')
	Image_var=np.where(Image_var>Maximum_valid_DN,np.nan,Image_var)
	Image_var=np.where(Image_var<Minimum_valid_DN,np.nan,Image_var)

	#値を求める
	Value_arr=Slope*Image_var+Offset
	Value_arr=np.array(Value_arr,dtype='float32')

	#列数
	lin_size=Image_var.shape[1]
	#行数
	col_size=Image_var.shape[0]

	#GCPのリストをつくる
	#L2の場合
	gcp_list=get_L2_geomesh(hdf_filename,lin_size,col_size)

	#出力
	dtype = gdal.GDT_Float32
	band=1
	output = gdal.GetDriverByName('GTiff').Create(output_file,lin_size,col_size,band,dtype) 
	output.GetRasterBand(1).WriteArray(Value_arr)
	wkt = output.GetProjection()
	output.SetGCPs(gcp_list,wkt)
	#与えたGCPを使ってESRI53008に投影変換
#			dstSRS='+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371000 +b=6371000 +units=m +no_defs',\
	output = gdal.Warp(output_file, \
			output, \
			dstSRS='ESRI:53008',\
			srcNodata=np.nan,\
			dstNodata=np.nan,\
			tps = True, \
			outputType=dtype,\
			multithread=True,\
			resampleAlg=gdalconst.GRIORA_NearestNeighbour)
	output.FlushCache()
	output = None 	
	print('CREATE '+output_file)

#CLOSE HDF FILE
	Image_var=None	
	hdf_file=None
