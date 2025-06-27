import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import base64
import io
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# 初始化Dash应用
app = dash.Dash(__name__)

# 定义样式
CARD_STYLE = {
    'border': '1px solid #e0e0e0',
    'borderRadius': '8px',
    'padding': '20px',
    'margin': '10px 0',
    'backgroundColor': '#ffffff',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
}

SECTION_TITLE_STYLE = {
    'color': '#2c3e50',
    'fontSize': '20px',
    'fontWeight': 'bold',
    'marginBottom': '15px',
    'borderBottom': '2px solid #3498db',
    'paddingBottom': '5px'
}

INPUT_STYLE = {
    'width': '100%',
    'padding': '8px',
    'borderRadius': '4px',
    'border': '1px solid #ddd'
}

BUTTON_STYLE = {
    'backgroundColor': '#3498db',
    'color': 'white',
    'padding': '12px 30px',
    'border': 'none',
    'borderRadius': '6px',
    'fontSize': '16px',
    'fontWeight': 'bold',
    'cursor': 'pointer',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.2)'
}

app.layout = html.Div([
    dcc.Store(id='stored-data'),
    dcc.Store(id='processed-data'),

    # 标题
    html.Div([
        html.H1("📊 时间序列数据分析看板",
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'})
    ]),

    # 第一步：文件上传
    html.Div([
        html.H3("📁 第一步：文件上传", style=SECTION_TITLE_STYLE),

        dcc.Upload(
            id='upload-data',
            children=html.Div([
                '🔄 拖拽文件到此处或 ',
                html.A('点击选择文件', style={'color': '#3498db', 'textDecoration': 'underline'})
            ]),
            style={
                'width': '100%',
                'height': '80px',
                'lineHeight': '80px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '8px',
                'textAlign': 'center',
                'backgroundColor': '#f8f9fa',
                'borderColor': '#3498db',
                'fontSize': '16px'
            },
            multiple=False
        ),

        html.Div([
            html.Div([
                html.Label("文件编码格式:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='encoding-dropdown',
                    options=[
                        {'label': 'UTF-8 (推荐)', 'value': 'utf-8'},
                        {'label': 'UTF-8-SIG', 'value': 'utf-8-sig'},
                        {'label': 'UTF-16', 'value': 'utf-16'},
                        {'label': 'GBK (中文)', 'value': 'gbk'},
                        {'label': 'GB2312', 'value': 'gb2312'},
                        {'label': 'ISO-8859-1', 'value': 'iso-8859-1'},
                    ],
                    value='utf-8',
                    style={'width': '250px'}
                )
            ], style={'display': 'inline-block', 'verticalAlign': 'top'}),

            html.Div([
                html.Div(id='upload-status', style={'marginLeft': '20px'})
            ], style={'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '20px'})
        ], style={'marginTop': '15px'})
    ], style=CARD_STYLE),

    # 第二步：数据配置（初始隐藏）
    html.Div([
        html.H3("⚙️ 第二步：数据配置", style=SECTION_TITLE_STYLE),

        # 数据预览
        html.Div([
            html.H4("📋 数据预览", style={'color': '#34495e', 'marginBottom': '10px'}),
            html.Div(id='data-preview-table')
        ], style={'marginBottom': '25px'}),

        # 数据统计
        html.Div([
            html.H4("📊 数据统计", style={'color': '#34495e', 'marginBottom': '10px'}),
            html.Div(id='data-describe')
        ], style={'marginBottom': '25px'}),

        # 配置区域 - 使用网格布局
        html.Div([
            # 第一行：日期时间配置 和 数据聚合配置
            html.Div([
                # 日期时间配置
                html.Div([
                    html.H4("📅 日期时间配置", style={'color': '#e74c3c', 'marginBottom': '15px'}),

                    html.Div([
                        html.Label("主日期列:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='date-column-dropdown',
                            placeholder="选择日期列...",
                            style=INPUT_STYLE
                        )
                    ], style={'marginBottom': '15px'}),

                    html.Div([
                        html.Label("时间列(可选):", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='time-column-dropdown',
                            placeholder="选择时间列...",
                            style=INPUT_STYLE
                        )
                    ], style={'marginBottom': '15px'}),

                    dcc.Checklist(
                        id='datetime-options',
                        options=[
                            {'label': ' 合并日期和时间列', 'value': 'merge_datetime'},
                            {'label': ' 处理24:00时间格式', 'value': 'handle_24hour'}
                        ],
                        value=['handle_24hour'],
                        style={'fontSize': '14px'},
                        labelStyle={'display': 'block', 'marginBottom': '8px'}
                    )
                ], style={
                    'border': '1px solid #e74c3c',
                    'borderRadius': '6px',
                    'padding': '20px',
                    'backgroundColor': '#fdf2f2'
                }),

                # 数据聚合配置
                html.Div([
                    html.H4("🔄 数据聚合配置", style={'color': '#9b59b6', 'marginBottom': '15px'}),

                    html.Div([
                        html.Label("时间粒度:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='time-resolution-dropdown',
                            options=[
                                {'label': '原始数据', 'value': 'raw'},
                                {'label': '15分钟', 'value': '15min'},
                                {'label': '1小时', 'value': '1H'},
                                {'label': '1日', 'value': '1D'},
                                {'label': '1周', 'value': '1W'},
                                {'label': '1月', 'value': '1M'}
                            ],
                            value='raw',
                            style=INPUT_STYLE
                        )
                    ], style={'marginBottom': '15px'}),

                    html.Div([
                        html.Label("聚合方式:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='agg-method-dropdown',
                            options=[
                                {'label': '均值', 'value': 'mean'},
                                {'label': '最后值', 'value': 'last'},
                                {'label': '加总', 'value': 'sum'},
                                {'label': '最大值', 'value': 'max'},
                                {'label': '最小值', 'value': 'min'}
                            ],
                            value='mean',
                            style=INPUT_STYLE
                        )
                    ], style={'marginBottom': '15px'}),

                    # 季节图聚合方式
                    html.Div([
                        html.Label("季节图聚合方式:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='seasonal-agg-dropdown',
                            options=[
                                {'label': '月度聚合', 'value': 'monthly'},
                                {'label': '日度聚合', 'value': 'daily'}
                            ],
                            value='monthly',
                            style=INPUT_STYLE
                        )
                    ], style={'marginBottom': '15px'}),

                    # 前向填充选项
                    dcc.Checklist(
                        id='ffill-checkbox',
                        options=[{'label': ' 使用前向填充处理缺失值', 'value': 'ffill'}],
                        value=[],
                        style={'fontSize': '14px'}
                    )
                ], style={
                    'border': '1px solid #9b59b6',
                    'borderRadius': '6px',
                    'padding': '20px',
                    'backgroundColor': '#f8f5ff'
                })
            ], style={
                'display': 'grid',
                'gridTemplateColumns': '1fr 1fr',
                'gap': '20px',
                'marginBottom': '20px'
            }),

            # 第二行：分析字段选择 和 时间筛选
            html.Div([
                # 分析字段选择
                html.Div([
                    html.H4("🎯 分析字段选择", style={'color': '#27ae60', 'marginBottom': '15px'}),
                    dcc.Dropdown(
                        id='analysis-fields-dropdown',
                        placeholder="选择要分析的数值字段...",
                        multi=False,
                        style=INPUT_STYLE
                    )
                ], style={
                    'border': '1px solid #27ae60',
                    'borderRadius': '6px',
                    'padding': '20px',
                    'backgroundColor': '#f0f9f4'
                }),

                # 时间筛选
                html.Div([
                    html.H4("📆 时间筛选", style={'color': '#f39c12', 'marginBottom': '15px'}),

                    html.Div([
                        html.Label("年份选择:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='year-filter-dropdown',
                            placeholder="选择年份...",
                            multi=True,
                            style=INPUT_STYLE
                        )
                    ], style={'marginBottom': '15px'}),

                    html.Div([
                        html.Label("月份选择:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='month-filter-dropdown',
                            options=[{'label': f'{i}月', 'value': i} for i in range(1, 13)],
                            placeholder="选择月份...",
                            multi=True,
                            style=INPUT_STYLE
                        )
                    ])
                ], style={
                    'border': '1px solid #f39c12',
                    'borderRadius': '6px',
                    'padding': '20px',
                    'backgroundColor': '#fef9e7'
                })
            ], style={
                'display': 'grid',
                'gridTemplateColumns': '1fr 1fr',
                'gap': '20px',
                'marginBottom': '20px'
            }),

            # 第三行：数据筛选
            html.Div([
                html.H4("🔍 数据筛选", style={'color': '#e67e22', 'marginBottom': '15px'}),

                html.Div([
                    html.Div([
                        html.Label("筛选字段:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='filter-field-dropdown',
                            placeholder="选择筛选字段...",
                            style=INPUT_STYLE
                        )
                    ], style={'width': '30%', 'display': 'inline-block'}),

                    html.Div([
                        html.Label("筛选条件:", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='filter-condition-dropdown',
                            options=[
                                {'label': '等于', 'value': '=='},
                                {'label': '大于', 'value': '>'},
                                {'label': '小于', 'value': '<'},
                                {'label': '大于等于', 'value': '>='},
                                {'label': '小于等于', 'value': '<='},
                                {'label': '不等于', 'value': '!='}
                            ],
                            value='==',
                            style=INPUT_STYLE
                        )
                    ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '5%'}),

                    html.Div([
                        html.Label("筛选值:", style={'fontWeight': 'bold'}),
                        dcc.Input(
                            id='filter-value-input',
                            type='text',
                            placeholder='输入筛选值',
                            style=INPUT_STYLE
                        )
                    ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '5%'})
                ], style={'marginBottom': '15px'}),

                dcc.Checklist(
                    id='enable-filter-checkbox',
                    options=[{'label': ' 启用数据筛选', 'value': 'enable'}],
                    value=[],
                    style={'fontSize': '14px', 'fontWeight': 'bold'}
                )
            ], style={
                'border': '1px solid #e67e22',
                'borderRadius': '6px',
                'padding': '20px',
                'backgroundColor': '#fdf6e3'
            })
        ]),

        # 处理按钮
        html.Div([
            html.Button(
                '🚀 处理数据并生成图表',
                id='process-button',
                n_clicks=0,
                style=BUTTON_STYLE
            )
        ], style={'textAlign': 'center', 'marginTop': '30px'})

    ], id='data-config-section', style={**CARD_STYLE, 'display': 'none'}),

    # 第三步：图表展示区域
    html.Div(id='charts-section', children=[], style={'display': 'none'})
])


# 文件上传处理
@app.callback(
    [Output('stored-data', 'data'),
     Output('upload-status', 'children'),
     Output('data-config-section', 'style'),
     Output('date-column-dropdown', 'options'),
     Output('time-column-dropdown', 'options'),
     Output('analysis-fields-dropdown', 'options'),
     Output('filter-field-dropdown', 'options'),
     Output('data-preview-table', 'children')],
    [Input('upload-data', 'contents'),
     Input('encoding-dropdown', 'value')],
    [State('upload-data', 'filename')]
)
def handle_file_upload(contents, encoding, filename):
    if contents is None:
        return None, "", {'display': 'none'}, [], [], [], [], ""

    try:
        # 解析文件内容
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # 根据文件类型读取数据
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode(encoding)))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None, html.Div("不支持的文件格式", style={'color': 'red'}), {'display': 'none'}, [], [], [], ""

        # 存储原始数据
        stored_data = df.to_json(date_format='iso', orient='split')

        # 检测可能的日期列
        date_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', '日期', '时间', 'datetime']):
                date_columns.append(col)

        # 检测数值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        # 创建选项
        all_column_options = [{'label': col, 'value': col} for col in df.columns]
        date_column_options = all_column_options
        time_column_options = all_column_options + [{'label': '无', 'value': 'None'}]
        numeric_options = [{'label': col, 'value': col} for col in numeric_columns]

        # 数据预览表格
        preview_table = dash_table.DataTable(
            data=df.head(10).to_dict('records'),
            columns=[{"name": i, "id": i} for i in df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px', 'fontSize': '14px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold', 'fontSize': '15px'}
        )

        status = html.Div([
            html.P(f"✅ 文件上传成功: {filename}", style={'color': 'green'}),
            html.P(f"数据形状: {df.shape[0]} 行 × {df.shape[1]} 列")
        ])

        return (stored_data, status, {'display': 'block'},
                date_column_options, time_column_options, numeric_options, all_column_options, preview_table)

    except Exception as e:
        return (None, html.Div(f"❌ 文件读取失败: {str(e)}", style={'color': 'red'}),
                {'display': 'none'}, [], [], [], [], "")


# 自动选择默认值
@app.callback(
    [Output('date-column-dropdown', 'value'),
     Output('analysis-fields-dropdown', 'value')],
    [Input('date-column-dropdown', 'options'),
     Input('analysis-fields-dropdown', 'options')]
)
def set_default_values(date_options, numeric_options):
    # 自动选择第一个日期相关的列
    date_value = None
    if date_options:
        for option in date_options:
            col_name = option['label'].lower()
            if any(keyword in col_name for keyword in ['date', 'time', '日期', '时间', 'datetime']):
                date_value = option['value']
                break
        if date_value is None:
            date_value = date_options[0]['value'] if date_options else None

    # 自动选择前3个数值列
    numeric_values = []
    if numeric_options:
        numeric_values = numeric_options[0]['value']

    return date_value, numeric_values


# 更新数据统计信息
@app.callback(
    Output('data-describe', 'children'),
    [Input('stored-data', 'data')]
)
def update_data_describe(stored_data):
    if stored_data is None:
        return ""

    try:
        df = pd.read_json(stored_data, orient='split')

        # 生成描述性统计
        desc = df.describe()

        return dash_table.DataTable(
            data=desc.round(2).reset_index().to_dict('records'),
            columns=[{"name": i, "id": i} for i in desc.reset_index().columns],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px', 'fontSize': '14px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold', 'fontSize': '15px'}
        )
    except:
        return "无法生成统计信息"


# 更新年份选择选项
@app.callback(
    Output('year-filter-dropdown', 'options'),
    [Input('stored-data', 'data'),
     Input('date-column-dropdown', 'value')]
)
def update_year_options(stored_data, date_column):
    if stored_data is None or date_column is None:
        return []

    try:
        df = pd.read_json(stored_data, orient='split')
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        years = sorted(df[date_column].dt.year.dropna().unique())
        return [{'label': str(year), 'value': year} for year in years]
    except:
        return []


# 数据处理和图表生成
@app.callback(
    [Output('processed-data', 'data'),
     Output('charts-section', 'children'),
     Output('charts-section', 'style')],
    [Input('process-button', 'n_clicks')],
    [State('stored-data', 'data'),
     State('date-column-dropdown', 'value'),
     State('time-column-dropdown', 'value'),
     State('datetime-options', 'value'),
     State('time-resolution-dropdown', 'value'),
     State('agg-method-dropdown', 'value'),
    State('seasonal-agg-dropdown', 'value'),  # 新增
     State('ffill-checkbox', 'value'),  # 新增
     State('analysis-fields-dropdown', 'value'),
     State('year-filter-dropdown', 'value'),
     State('month-filter-dropdown', 'value'),
     State('filter-field-dropdown', 'value'),  # 新增
     State('filter-condition-dropdown', 'value'),  # 新增
     State('filter-value-input', 'value'),  # 新增
     State('enable-filter-checkbox', 'value')
]
)
def process_data_and_generate_charts(n_clicks, stored_data, date_column, time_column,
                                     datetime_options, time_resolution, agg_method,
                                        seasonal_agg, use_ffill,
                                     analysis_fields, selected_years, selected_months,
                                   filter_field, filter_condition, filter_value, enable_filter):
    if n_clicks == 0 or stored_data is None or date_column is None or not analysis_fields:
        return None, [], {'display': 'none'}

    try:
        # 读取数据
        df = pd.read_json(stored_data, orient='split')

        # 处理日期时间
        df = process_datetime(df, date_column, time_column, datetime_options)

        # 前向填充处理（在聚合之前）
        if use_ffill and 'ffill' in use_ffill:
            if isinstance(analysis_fields, str):
                df[analysis_fields] = df[analysis_fields].fillna(method='ffill')
            else:
                for field in analysis_fields:
                    if field in df.columns:
                        df[field] = df[field].fillna(method='ffill')

        # 时间筛选
        if selected_years:
            df = df[df['datetime'].dt.year.isin(selected_years)]
        if selected_months:
            df = df[df['datetime'].dt.month.isin(selected_months)]

        # 数据筛选
        if enable_filter and 'enable' in enable_filter and filter_field and filter_value:
            try:
                # 尝试转换为数值
                try:
                    filter_val = float(filter_value)
                except:
                    filter_val = filter_value  # 保持字符串

                # 应用筛选条件
                if filter_condition == '==':
                    df = df[df[filter_field] == filter_val]
                elif filter_condition == '>':
                    df = df[df[filter_field] > filter_val]
                elif filter_condition == '<':
                    df = df[df[filter_field] < filter_val]
                elif filter_condition == '>=':
                    df = df[df[filter_field] >= filter_val]
                elif filter_condition == '<=':
                    df = df[df[filter_field] <= filter_val]
                elif filter_condition == '!=':
                    df = df[df[filter_field] != filter_val]
            except Exception as filter_error:
                error_msg = html.Div(f"⚠️ 数据筛选失败: {str(filter_error)}",
                                     style={'color': 'orange', 'padding': '20px'})
                return None, [error_msg], {'display': 'block'}

        # 检查筛选后是否还有数据
        if len(df) == 0:
            error_msg = html.Div("⚠️ 筛选后没有数据，请调整筛选条件", style={'color': 'orange', 'padding': '20px'})
            return None, [error_msg], {'display': 'block'}

        # 数据聚合
        if time_resolution != 'raw':
            df = aggregate_data(df, time_resolution, agg_method, analysis_fields)

        # 生成图表
        charts = generate_all_charts(df, analysis_fields, time_resolution, seasonal_agg)

        return df.to_json(date_format='iso', orient='split'), charts, {'display': 'block'}

    except Exception as e:
        error_msg = html.Div(f"❌ 数据处理失败: {str(e)}", style={'color': 'red', 'padding': '20px'})
        return None, [error_msg], {'display': 'block'}


def process_datetime(df, date_column, time_column, options):
    """处理日期时间"""

    # 处理主日期列
    df['datetime'] = pd.to_datetime(df[date_column], errors='coerce')

    # 如果有时间列且选择了合并
    if time_column and time_column != 'None' and 'merge_datetime' in (options or []):
        try:
            # 处理时间列 - 关键修复部分
            time_series = df[time_column].copy()

            # 检查时间列的格式
            if pd.api.types.is_numeric_dtype(time_series):
                # 如果是数字，假设是小时数，转换为HH:00:00格式
                time_series = time_series.astype(int).astype(str) + ':00:00'
                print(f"检测到数字时间列，转换为时间格式: {time_series.head().tolist()}")
            else:
                # 如果是字符串，先处理24:00的情况
                time_series = time_series.astype(str)
                if 'handle_24hour' in (options or []):
                    time_series = time_series.str.replace('24:00', '23:59:59')
                    time_series = time_series.str.replace('24:00:00', '23:59:59')

            # 合并日期和时间
            datetime_str = df[date_column].astype(str) + ' ' + time_series.astype(str)
            merged_datetime = pd.to_datetime(datetime_str, errors='coerce')

            # 检查合并结果
            valid_count = merged_datetime.notna().sum()
            total_count = len(merged_datetime)

            if valid_count > total_count * 0.5:  # 如果超过50%的数据有效，使用合并结果
                df['datetime'] = merged_datetime
                print(f"成功合并日期时间: {valid_count}/{total_count} 条记录有效")
            else:
                print(f"合并失败，有效记录太少: {valid_count}/{total_count}，使用原日期列")

        except Exception as e:
            print(f"日期时间合并出错: {str(e)}，使用原日期列")

    # 删除无效的日期时间
    original_count = len(df)
    df = df.dropna(subset=['datetime'])
    final_count = len(df)

    if final_count < original_count:
        print(f"删除了 {original_count - final_count} 条无效日期时间记录")

    if final_count == 0:
        raise ValueError("所有日期时间数据都无效，请检查日期时间列的格式")

    # 添加时间相关的辅助列
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    df['day'] = df['datetime'].dt.day
    df['hour'] = df['datetime'].dt.hour
    df['minute'] = df['datetime'].dt.minute
    df['weekday'] = df['datetime'].dt.weekday
    df['dayofyear'] = df['datetime'].dt.dayofyear

    return df.sort_values('datetime')


def aggregate_data(df, time_resolution, agg_method, analysis_fields):
    """数据聚合"""

    # 设置datetime为索引
    df_agg = df.set_index('datetime')

    # 选择要聚合的列
    if isinstance(analysis_fields, str):
        cols_to_agg = [analysis_fields]
    else:
        cols_to_agg = analysis_fields

    # 只聚合数值列
    numeric_cols = df_agg.select_dtypes(include=[np.number]).columns
    cols_to_agg = [col for col in cols_to_agg if col in numeric_cols]

    if not cols_to_agg:
        return df

    # 聚合数据
    if agg_method == 'mean':
        df_result = df_agg[cols_to_agg].resample(time_resolution).mean()
    elif agg_method == 'sum':
        df_result = df_agg[cols_to_agg].resample(time_resolution).sum()
    elif agg_method == 'last':
        df_result = df_agg[cols_to_agg].resample(time_resolution).last()
    elif agg_method == 'max':
        df_result = df_agg[cols_to_agg].resample(time_resolution).max()
    elif agg_method == 'min':
        df_result = df_agg[cols_to_agg].resample(time_resolution).min()
    else:
        df_result = df_agg[cols_to_agg].resample(time_resolution).mean()

    # 重置索引并重新添加时间辅助列
    df_result = df_result.reset_index()
    df_result['year'] = df_result['datetime'].dt.year
    df_result['month'] = df_result['datetime'].dt.month
    df_result['day'] = df_result['datetime'].dt.day
    df_result['hour'] = df_result['datetime'].dt.hour
    df_result['minute'] = df_result['datetime'].dt.minute
    df_result['weekday'] = df_result['datetime'].dt.weekday
    df_result['dayofyear'] = df_result['datetime'].dt.dayofyear

    return df_result


def generate_all_charts(df, analysis_fields, time_resolution, seasonal_agg='monthly'):
    """生成所有图表"""

    charts = []

    charts.append(html.H3("3. 数据分析结果"))

    # 处理单个字段
    field = analysis_fields[0] if isinstance(analysis_fields, list) else analysis_fields

    if field not in df.columns:
        return [html.Div("❌ 选择的字段不存在于数据中", style={'color': 'red', 'padding': '20px'})]

    charts.append(html.H4(f"字段: {field}"))

    # 时间序列图
    fig_ts = create_time_series_chart(df, field)
    charts.append(dcc.Graph(figure=fig_ts))

    # 季节图和直方图并排
    fig_seasonal = create_seasonal_chart(df, field, time_resolution, seasonal_agg)
    fig_hist = create_histogram_chart(df, field)

    charts.append(html.Div([
        html.Div([
            dcc.Graph(figure=fig_seasonal)
        ], style={'width': '60%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(figure=fig_hist)
        ], style={'width': '40%', 'display': 'inline-block'})
    ]))

    # 日内图（如果有小时数据）
    if 'hour' in df.columns and df['hour'].nunique() > 1:
        fig_daily = create_daily_pattern_chart(df, field)
        charts.append(dcc.Graph(figure=fig_daily))

    charts.append(html.Hr())

    return charts


def create_time_series_chart(df, field):
    """创建时间序列图"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['datetime'],
        y=df[field],
        mode='lines',
        name=field,
        line=dict(width=1)
    ))

    fig.update_layout(
        title=f'{field} - 时间序列图',
        xaxis_title='时间',
        yaxis_title=field,
        template='plotly_white',
        height=400,
        font=dict(size=14),
        title_font=dict(size=16)
    )

    return fig


def create_seasonal_chart(df, field, time_resolution, seasonal_agg='monthly'):
    """创建季节图 - 根据聚合方式调整显示"""
    fig = go.Figure()

    # 获取所有年份
    years = sorted(df['year'].unique(), reverse=True)

    if len(years) == 0:
        fig.update_layout(title=f'{field} - 季节性变化图 (无数据)')
        return fig

    # 根据季节图聚合方式决定分组方式
    if seasonal_agg == 'daily':
        # 日度聚合：按年内天数聚合
        group_by = 'dayofyear'
        x_tickvals = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
        x_ticktext = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
        mode = 'lines'  # 只显示线条
        marker_size = 0  # 不显示点
    else:  # monthly
        # 月度聚合：按月份聚合
        group_by = 'month'
        x_tickvals = list(range(1, 13))
        x_ticktext = [f'{i}月' for i in range(1, 13)]
        mode = 'lines+markers'  # 显示线条和点
        marker_size = 8  # 显示点

    # 1. 先添加各年数据traces（作为背景层）
    colors = px.colors.qualitative.Set1
    year_traces = []

    for i, year in enumerate(years[:8]):  # 显示最近8年
        try:
            year_data = df[df['year'] == year]
            year_data = year_data[year_data[field].notna()]
            if len(year_data) > 0:
                year_grouped = year_data.groupby(group_by)[field].mean()
                if len(year_grouped) > 0:
                    is_recent = i < 2
                    current_marker_size = (6 if is_recent else 4) if marker_size > 0 else 0

                    # 最新年份使用红色，加粗显示
                    if i == 0:  # 最新年份
                        line_color = 'red'
                        line_width = 4
                    else:
                        line_color = colors[i % len(colors)]
                        line_width = 3 if is_recent else 1.5

                    trace = go.Scatter(
                        x=year_grouped.index,
                        y=year_grouped.values,
                        mode=mode,
                        name=f'{year}年',
                        line=dict(
                            color=line_color,
                            width=line_width
                        ),
                        marker=dict(size=current_marker_size) if current_marker_size > 0 else dict(),
                        legendrank=i + 2  # 从2开始，为均值留出第1位
                    )
                    fig.add_trace(trace)
        except Exception as e:
            print(f"处理 {year} 年数据失败: {e}")
            continue

    # 2. 最后添加历年平均值trace（作为前景层，确保不被覆盖）
    try:
        valid_data = df[df[field].notna()]
        if len(valid_data) > 0:
            mean_by_period = valid_data.groupby(group_by)[field].mean()
            if len(mean_by_period) > 0:
                fig.add_trace(go.Scatter(
                    x=mean_by_period.index,
                    y=mean_by_period.values,
                    mode=mode,
                    name='历年平均值',
                    line=dict(color='black', width=4),  # 加粗黑线
                    marker=dict(size=marker_size + 2, color='black') if marker_size > 0 else dict(),
                    legendrank=1,  # 设置为第一优先级
                    # 确保这条线在最上层显示
                    opacity=1.0
                ))
    except Exception as e:
        print(f"计算平均值失败: {e}")

    fig.update_layout(
        title=f'{field} - 季节性变化图 ({seasonal_agg})',
        template='plotly_white',
        height=600,  # 增加高度以容纳底部图例
        # 图例设置：放在底部，水平排列
        legend=dict(
            orientation="h",  # 水平排列
            yanchor="top",
            y=-0.12,  # 放在图表下方
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1,
            traceorder='normal',  # 按添加顺序显示图例
            font=dict(size=12),
            itemsizing='constant'
        ),
        # 调整边距以容纳底部图例
        margin=dict(
            l=60,
            r=60,
            t=80,
            b=120  # 增加底部边距
        ),
        font=dict(size=14),
        title_font=dict(size=16),
        xaxis=dict(
            tickvals=x_tickvals,
            ticktext=x_ticktext
        )
    )

    return fig

def create_daily_pattern_chart(df, field):
    """创建日内模式图 - 显示每天的数据"""
    fig = go.Figure()

    # 获取所有日期
    df['date_str'] = df['datetime'].dt.strftime('%Y-%m-%d')
    dates = sorted(df['date_str'].unique())

    # 限制显示最近30天，避免图表过于拥挤
    recent_dates = dates[-30:] if len(dates) > 30 else dates

    # 先添加所有天的平均值（放在最上面）
    try:
        valid_data = df[df[field].notna()]
        if len(valid_data) > 0:
            hourly_mean = valid_data.groupby('hour')[field].mean().reset_index()
            if len(hourly_mean) > 0:
                fig.add_trace(go.Scatter(
                    x=hourly_mean['hour'],
                    y=hourly_mean[field],
                    mode='lines+markers',
                    name='所有天平均值',
                    line=dict(color='red', width=3),
                    marker=dict(size=6),
                    visible=True,  # 平均值始终显示
                    legendrank=1
                ))
    except Exception as e:
        print(f"计算小时平均值失败: {e}")

    # 为每一天添加一条线（按日期倒序）
    colors = px.colors.qualitative.Set3
    recent_dates_desc = list(reversed(recent_dates))  # 倒序排列

    for i, date in enumerate(recent_dates_desc):
        try:
            day_data = df[df['date_str'] == date].sort_values('hour')
            day_data = day_data[day_data[field].notna()]
            if len(day_data) > 0:
                # 前5个（最近的日期）默认显示，其余隐藏
                is_visible = True if i < 5 else 'legendonly'

                fig.add_trace(go.Scatter(
                    x=day_data['hour'],
                    y=day_data[field],
                    mode='lines+markers',
                    name=date,
                    line=dict(color=colors[i % len(colors)], width=1.5),
                    marker=dict(size=4),
                    visible=is_visible,
                    legendrank=i + 2
                ))
        except Exception as e:
            print(f"处理日期 {date} 失败: {e}")
            continue

    fig.update_layout(
        title=f'{field} - 日内变化模式',
        xaxis_title='小时',
        yaxis_title=field,
        template='plotly_white',
        height=600,  # 增加高度以容纳底部图例
        # 图例设置：放在底部，水平排列，多行显示
        legend=dict(
            orientation="h",  # 水平排列
            yanchor="top",
            y=-0.15,  # 放在图表下方
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1,
            traceorder='normal',  # 按添加顺序显示图例
            # 设置图例项的间距和换行
            itemsizing='constant',
            itemwidth=30,
            # 允许图例换行显示
            font=dict(size=11)
        ),
        # 调整边距以容纳底部图例
        margin=dict(
            l=50,
            r=50,
            t=80,
            b=150  # 增加底部边距，因为可能有多行图例
        ),
        font=dict(size=14),
        title_font=dict(size=16),
        xaxis=dict(
            tickvals=list(range(0, 24, 2)),
            ticktext=[f'{i}:00' for i in range(0, 24, 2)]
        )
    )

    return fig


def create_histogram_chart(df, field):
    """创建直方图"""
    fig = go.Figure()

    # 过滤掉NaN值
    data = df[field].dropna()

    if len(data) > 0:
        fig.add_trace(go.Histogram(
            x=data,
            nbinsx=30,
            name=field,
            opacity=0.7
        ))

    fig.update_layout(
        title=f'{field} - 数据分布直方图',
        xaxis_title=field,
        yaxis_title='频次',
        template='plotly_white',
        height=550,
        font=dict(size=14),
        title_font=dict(size=16)
    )

    return fig


if __name__ == '__main__':
    app.run(debug=True, port=8050)
