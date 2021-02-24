# coding:utf-8
import numpy as np
import sys
import gdal,gdalconst,osr

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
		
	#求めたりタイル番号の左上画素の中心の緯度[deg]は、
	#1タイルあたりの角度が10[deg]であることから、
	lat0=90.0-vtile*10

	#求めたいタイル番号の左上画素の中心の経度[deg]は、
	#1タイルあたりの角度が10[deg]であることから、
	lon0=-180.0+htile*10

	UL_X,UL_Y=6371007.181*np.radians(lon0),6371007.181*np.radians(lat0)
	resolution=6371007.181*2*np.pi/(htilenum*coltile)

	return UL_X,UL_Y,resolution
 

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


	DN=gdal.Open(hdf_file.GetSubDatasets()[dataset_index][0], gdal.GA_ReadOnly).ReadAsArray()

	#Get Sole, Offset,Minimum_valid_DN, Maximum_valid_DN
	Metadata=hdf_file.GetMetadata_Dict()
	hdf_filename=Metadata['Global_attributes_Product_file_name']

	Slope=None
	Offset=None
	Mask=None
	Minimum_valid_DN=None
	Maximum_valid_DN=None
	Data_description=None
	for metadata_lavel in Metadata.keys():
		if band_name+'_Slope' in metadata_lavel:
			Slope=float(Metadata[metadata_lavel])
		if band_name+'_Offset' in metadata_lavel:
			Offset=float(Metadata[metadata_lavel])
		if (metadata_lavel is not band_name+'_Mask_for_statistics') and (band_name+'_Mask'in metadata_lavel): 
			Mask=float(Metadata[metadata_lavel])
		if band_name+'_Minimum_valid_DN' in metadata_lavel:
			Minimum_valid_DN=float(Metadata[metadata_lavel])
		if band_name+'_Maximum_valid_DN' in metadata_lavel:
			Maximum_valid_DN=float(Metadata[metadata_lavel])
		if band_name+'_Data_description' in metadata_lavel:
			Data_description=Metadata[metadata_lavel]
	#型変換とエラー値をnanに変換する
	DN=np.array(DN,dtype='uint16')
	if Mask is not None:
		Mask=np.array(Mask,dtype='uint16')
		DN=DN & Mask
	if((Maximum_valid_DN is not None) and (Minimum_valid_DN is not None)):
		DN=np.where(DN>=Maximum_valid_DN,np.nan,DN)
		DN=np.where(DN<=Minimum_valid_DN,np.nan,DN)

	#値を求める
	if((Slope is not None) and (Offset is not None)):
		Value_arr=Slope*DN+Offset
	Value_arr=np.array(Value_arr,dtype='float32')

	#列数
	lin_size=DN.shape[1]
	#行数
	col_size=DN.shape[0]

	#GCPのリストをつくる
	#L2の場合
	UL_X,UL_Y,ds=get_L2_geomesh(hdf_filename,lin_size,col_size)

	#出力
	dtype = gdal.GDT_Float32
	band=1
	output = gdal.GetDriverByName('GTiff').Create(output_file,lin_size,col_size,band,dtype)
	output.GetRasterBand(1).WriteArray(Value_arr)
	output.SetGeoTransform((UL_X, ds, 0, UL_Y, 0,-1*ds))
	#projection
	srs = osr.SpatialReference()
#	srs.ImportFromESRI('PROJCS["Sphere_Sinusoidal",GEOGCS["GCS_Sphere",DATUM["D_Sphere",SPHEROID["Sphere",6371000,0]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Sinusoidal"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",0],UNIT["Meter",1]]')
#	srs.ImportFromProj4('+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371000 +b=6371000 +units=m +no_defs')
	srs.SetFromUserInput('ESRI:53008')
	output.SetProjection(srs.ExportToWkt())

	#Add Description
	output.SetMetadata({'Data_description':str(Data_description)})
	output.FlushCache()
	output = None 	
	print('CREATE '+output_file)

#CLOSE HDF FILE
	Image_var=None	
	hdf_file=None
