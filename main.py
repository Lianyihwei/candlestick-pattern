import pandas as pd
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import vectorbt as vbt
import talib

# external_stylesheets -> 設定theme為BOOTSTRAP
# meta_tags -> 設定RWD
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
            meta_tags=[{
                'name': 'viewport',
                'content': 'width=device-width, initial-scale=1.0'
            }])
server = app.server

# 建立測試pattern清單
patterns = ['CDLENGULFING', 'CDLDOJI', 'CDLHAMMER', 'CDL3WHITESOLDIERS', 'CDLHARAMICROSS', 'CDLHANGINGMAN', 'CDLSHOOTINGSTAR', 'CDL3BLACKCROWS', 'CDLDARKCLOUDCOVER', 'CDLRISEFALL3METHODS', 'CDLMORNINGDOJISTAR', 'CDLEVENINGDOJISTAR']

# app.layout ->設定頁面配置
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([html.H2('K線圖型態查詢', style={'textAlign': 'center'})],
                width=12,
                className='mt-5')
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Markdown('''
            使用說明：輸入股票代號就可以帶出近7日K線圖有沒有符合常用型態與趨勢 (台股請記得加上.tw 如 2330.tw)[股票代號查詢](https://finance.yahoo.com/lookup)  
            分析的型態列表如下：  **'CDLENGULFING', 'CDLDOJI', 'CDLHAMMER', 'CDL3WHITESOLDIERS', 'CDLHARAMICROSS', 'CDLHANGINGMAN', 'CDLSHOOTINGSTAR', 'CDL3BLACKCROWS', 'CDLDARKCLOUDCOVER', 'CDLRISEFALL3METHODS', 'CDLMORNINGDOJISTAR', 'CDLEVENINGDOJISTAR'**
        ''', link_target='_blank')
        ], width=12, className='p1')
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Input(id='stock_symbol',
                value='2330.TW',
                type='text',
                placeholder='2330.TW')
        ], width=4, className='mb-2 p-2'),
    ]),
    dbc.Row([
        dbc.Col([
            html.H4('Stock Cadlestick 趨勢形態'),
            html.Div(className="trend", children=[
                dcc.Markdown(id='pattern', children=[])
                ])
    ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H4('Stock Cadlestick 股票K線圖'),
            dcc.Graph(id='stock_chart', figure={}),
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Markdown('''
            本網站提供的K線圖趨勢型態分析計算模型使用Talib資料庫，製作目的為作者研究使用，並非是提供您專業投資建議或是指標。  
            如有任何建議歡迎[來信討論](lianyihwei@protonmail.com)
        ''')
        ], width=12, className='p1')
    ]),
])

# 設定callback參數，1input(股票代號)->2output(測試pattern結果及1個月K線圖)
@app.callback(
    [Output('pattern', 'children'), 
    Output('stock_chart', 'figure')],
    Input('stock_symbol', 'value')
    )

# dash無法處理pandas-df資料，改用vecotrbt取及OHLC的series格式再合成dataframe
# 迴圈代入每個pattern，如果有符合模式，格式化輸出存進trends_list空子串
# plotly.go 製圖
def update_stock_data(symbol):
    open = vbt.YFData.download(symbol, period='3mo', interval='1d',
                            missing_index='drop').get('Open')
    high = vbt.YFData.download(symbol, period='3mo', interval='1d',
                            missing_index='drop').get('High')
    low = vbt.YFData.download(symbol, period='3mo', interval='1d',
                            missing_index='drop').get('Low')
    close = vbt.YFData.download(symbol, period='3mo', interval='1d',
                            missing_index='drop').get('Close')
    volume = vbt.YFData.download(symbol, period='3mo', interval='1d',
                            missing_index='drop').get('Volume')
    df = pd.DataFrame(open, columns=['Open'])
    df = pd.concat([open, high, low, close, volume], axis=1, join='inner')
    df.index = df.index.strftime('%Y-%m-%d')
    count = 0
    trends_list = ''
    for pattern in patterns:
        pattern_fun= getattr(talib, pattern)
        result = pattern_fun(df.Open, df.High, df.Low, df.Close).tail(7)
        if  result[result == 100].to_list() != None:
            for i in result.index[result == 100].to_list():
                trends_list = trends_list+('{} 在 **{}** 符合 **{}** 上漲形態  \n'.format(symbol, i, pattern))
                count += 1
        elif  result.index[result == -100].to_list() != None:
            for i in result.index[result == 100].to_list():
                trends_list = trends_list+('{} **{}** 符合 **{}** 下跌形態  \n'.format(symbol, i, pattern))
                count += 1
    if count == 0:
        trends_list = trends_list+('{} 沒有明顯趨勢'.format(symbol))
    fig = go.Figure(go.Candlestick(x=df.index,
                                open=df["Open"],
                                high=df["High"],
                                low=df['Low'],
                                close=df['Close'],
                                name='Candlestick K線圖'))
    fig.update_layout(xaxis_rangeslider_visible=False, 
        margin=dict(l=20, r=20, b=20, t=20))
    fig.update_xaxes(rangeslider_visible=False, type='category')
    return trends_list, fig


if __name__ == '__main__':
    app.run_server(debug=True)