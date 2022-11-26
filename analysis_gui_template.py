"""
Targetフォルダーに解析対象ファイルがある場合、解析を行う
解析対象ファイルをSaveフォルダーに移動する
解析結果の画像、解析のまとめCSVファイルを作成してSaveフォルダーに格納

解析対象ファイルのフォーマットが異なる(例えば、xyの並びが異なる、ヘッダーがないなど）場合でも選べる様にする

初期設定ファイル（Toml形式）でTarget,Saveフォルダーをあらかじめ指定している。

"""

from pathlib import Path
import shutil
import time
import toml
import pandas as pd
import numpy as np
import PySimpleGUI as sg


# ---　ファイルを解析するクラス　（別ファイルに作成してもよい）
import datetime

def now_datetime(type=1):
    """
    日時を文字列で返す
    type1:通常表示 "%Y-%m-%d %H:%M:%S"
    type2:"%Y%m%d%H%M%S"
    type3:"%Y%m%d_%H%M%S"
    type4:Base_file_nameで使用する形式 "%Y%m%d%H%M"
    elae:日付のみ "%Y%m%d"
    :return:
    """
    now = datetime.datetime.now()
    if type == 1:
        now_string = now.strftime("%Y-%m-%d %H:%M:%S")
    elif type == 2:
        now_string = now.strftime("%Y%m%d%H%M%S")
    elif type == 3:
        now_string = now.strftime("%Y%m%d_%H%M%S")
    elif type == 4:
        now_string = now.strftime("%Y%m%d%H%M")
    elif type == 5:
        now_string = now.strftime("%m%d_%H:%M:%S")
    elif type == 6:
        now_string = now.strftime("%Y%m%d")    
    else:
        now_string = now

    return  now_string

class Analysis():
    """
    example:
        fname = r'./TARGET/data1.csv'
        test = Analysis(fname)
        test.read_file()
        test.estimate()
        print(test.meta)

    """
    
    def __init__(self,file):
        self.file = Path(file)
        
    def read_file(self):
        
        #Pandasのcsv読み込みを例に
        self.df = pd.read_csv(self.file)
        
    def estimate(self):
        # 解析結果を辞書型に格納 
        total =  np.sum(self.df.iloc[:,1]*2) # Intensityを2倍にして和を計算
        
        self.meta = {'file_name':self.file.stem,'data':total}     

# Analysis Classを継承しています。異なる動作をさせたいメソッドのみ記述
class AnalysisB(Analysis):
    
    def read_files(self):
        pass
        # with open(self.file) as f:
        #     s = f.read()
        # self.data = s 
 
       
# ------ ここからGUIプログラム

sg.theme('Light Blue 2')

#　設定ファイルをTOMLで用意している場合
try: 
    with open('./setfile.toml') as f:
        set_obj = toml.load(f)
except: #tomlファイルがない場合
    set_obj = {"target_folder":'',"save_folder":'','file_type':'type1'}
    

layout = [[sg.Text('Auto Analysis')],
            [sg.Text("Target Folder"), sg.InputText(f'{set_obj["target_folder"]}',size=(80,4), key="-a_folder-")],
            [sg.Text("Save   Folder"), sg.InputText(f'{set_obj["save_folder"]}',size=(80,4), key="-s_folder-")],
            [sg.Text('File type'), sg.Radio('Type A', group_id='0',  default=set_obj['file_type'] == 'type1', key='-1-'), 
             sg.Radio('Type B', group_id='0',default=set_obj['file_type'] == 'type2',key='-2-')],
            [sg.Button('Loop start',key='-begin-'), sg.Button('Loop stop',key='-stop-')],
            [sg.Cancel()],
            [sg.Output(size=(80, 20))],
          ]

window = sg.Window('Auto Analysis', layout, location=(100, 100), size=(500, 500), resizable=True) 

read_flag = 0

# 解析した値を保存するため。（適宜変更）
date_res = []
file_res = []
total_res = []

while True:
    event, values = window.read(timeout=1000,timeout_key='-timeout-')
    #　1000msおきに-timeout- event が呼び出されます（timeoutを適宜変更）

    if event == '-begin-':
        print('Loop Start')
        read_flag = 1
        read_path = Path(values['-a_folder-'])
        
        # Saveフォルダーがない場合は作成される。
        save_path = Path(values['-s_folder-'])
        save_path.mkdir(exist_ok=True)

    elif event == '-stop-':
        print('Loop Stop')
        read_flag = 0
    
    elif event in '-timeout-':

        if read_flag == 1:
            files = list(read_path.glob('*'))
            # print(files)
            
            if len(files) != 0:
                # 必要かどうか検討（対象フォルダーに完全にファイルが移動できていない場合には、エラーになる可能性があるので0.5秒待っている）
                time.sleep(0.5) 
                    
                for fi in files:
                    if values['-1-']: # Type A
                        tmp_ins = Analysis(fi)
                    elif values['-2-']: # Type B 
                        tmp_ins = AnalysisB(fi) 
                    
                        
                    tmp_ins.read_file() 
                    tmp_ins.estimate()
                    
                    f_name = tmp_ins.meta["file_name"]
             
                    
                    # Targetフォルダーにあるファイルを移動する
                    new_p = save_path / fi.name
                    
                    # 移動するフォルダーに同じ名前のデータがあるとエラーになるため、ファイルがあるか確かめる
                    # ファイルがある場合は削除
                    if new_p.exists(): 
                        new_p.unlink()
                        
                    # shutil.move(fi,save_path) # Python 3.7だとエラーになる。
                    # https://tec.citrussin.com/entry/2019/03/24/201649
                    shutil.move(fi,new_p) 
                    
                    # fi.rename(new_p)
                    treat_date = now_datetime(type=3)
                    print(f'{treat_date}, Calculate, fname : {f_name}')
                    
                    date_res.append(treat_date)
                    file_res.append(fi.name)
                    total_res.append(tmp_ins.meta["data"])

    
    elif event in (None, 'Cancel'):
        # 処理した結果をまとめてCSVに出力する。
        res_dict = {'date': date_res,'file':file_res, 'data':total_res}
        df = pd.DataFrame(res_dict)
        csv_save_path = save_path / f'{now_datetime(type=4)}.csv'
        df.to_csv(str(csv_save_path), index=False)

        break
    
window.close()