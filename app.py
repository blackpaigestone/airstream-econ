from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from src.model import scenario
from src.data_sources import SERIES,load

BASE=Path(__file__).parent
app=Dash(__name__,title='The Economics of Mobility')
server=app.server
COLORS={'ink':'#e8eee9','muted':'#9aa9a3','bg':'#0e1719','panel':'#182528','accent':'#9ed4bc','gold':'#e5bd79'}
app.index_string='''<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}<style>
body{margin:0;background:#0e1719;color:#e8eee9;font-family:Inter,Arial,sans-serif} .wrap{max-width:1220px;margin:auto;padding:30px 22px 80px}.eyebrow{letter-spacing:3px;color:#9ed4bc;font-size:12px;font-weight:700}.hero{font-size:clamp(36px,5vw,66px);letter-spacing:-2px;margin:14px 0 10px}.sub{color:#9aa9a3;line-height:1.6;max-width:850px}.panel{background:#182528;border:1px solid #2b3b3d;border-radius:18px;padding:22px;margin:16px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:15px}.metric{font-size:29px;font-weight:700;margin:9px 0;color:#e8eee9}.small{font-size:12px;color:#9aa9a3;line-height:1.6}.label{color:#9ed4bc;font-size:12px;letter-spacing:1px;text-transform:uppercase}.tabs{margin:28px 0}.dash-tab{background:#182528!important;color:#c4d0ca!important;border:0!important}.dash-tab--selected{border-bottom:3px solid #9ed4bc!important;color:white!important}.control{padding:12px 0}.control label{display:block;margin-bottom:8px;color:#d5dfd9;font-size:13px}h2{font-size:28px;margin:0 0 12px}a{color:#9ed4bc} .note{padding:14px;border-left:3px solid #e5bd79;background:#26302c;line-height:1.6}input{color:#0e1719} @media(max-width:600px){.wrap{padding:20px 12px}}
</style></head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>'''
def panel(*children):return html.Div(children,className='panel')
def metric(name,value,note):return html.Div([html.Div(name,className='label'),html.Div(value,className='metric'),html.Div(note,className='small')],className='panel')
def figure_style(fig):
    fig.update_layout(paper_bgcolor='#182528',plot_bgcolor='#182528',font_color='#e8eee9',margin=dict(l=35,r=20,t=35,b=40),legend=dict(orientation='h',y=-.25),hovermode='x unified')
    fig.update_xaxes(gridcolor='#2c3a3d');fig.update_yaxes(gridcolor='#2c3a3d');return fig

def historical():
    opts=[{'label':f'{label} ({key})','value':key} for key,label in SERIES.items()]
    return html.Div([html.H2('A generation apart'),html.P('Observed economic time series. No simulated historical values.',className='sub'),
       panel(html.Div('Choose an official series',className='label'),dcc.Dropdown(id='series',options=opts,value='USSTHPI',style={'color':'#172022'}),dcc.Graph(id='history-chart'),html.Div(id='history-source',className='small')),
       panel(html.H3('Research question'),html.P('Did housing acquisition costs rise faster than the earnings available to younger adults? Indexed series alone cannot answer this: our next research pass will integrate Census age-specific income, comparable housing-price concepts, and mortgage-payment burdens.'),html.P('Important: the median price of NEW homes sold is not the median value of all existing homes. Do not combine unlike populations without disclosure.',className='note'))])

def controls():
    specs=[('rate','Loan APR (%)',8,0,16,.5),('years','Loan term (years)',15,5,25,1),('campsite','Monthly site costs ($)',600,0,2000,50),('diesel','Monthly fuel ($)',350,0,1500,50),('other','Insurance, maintenance, utilities, internet ($/mo)',550,100,1800,50),('resale','Resale as % of purchase price',70,30,110,5),('upfront','Taxes, fees, setup ($)',0,0,25000,500)]
    return [html.Div([html.Label(label),dcc.Slider(min=lo,max=hi,step=step,value=val,id=key,tooltip={'placement':'bottom','always_visible':True})],className='control') for key,label,val,lo,hi,step in specs]

def housing():
    return html.Div([html.H2('The housing decision'),html.P('Illustrative assumptions. Loan principal is not double-counted as a cost; remaining debt and resale proceeds enter the net-cost calculation.',className='sub'),
      html.Div([panel(html.H3('Change the assumptions'),*controls()),panel(html.H3('Three-year outcome'),html.Div(id='scenario-metrics'),dcc.Graph(id='housing-chart'),html.Div(id='scenario-comment',className='small'))],className='grid')])

def valuation():
    fig=go.Figure()
    fig.add_trace(go.Bar(x=['J.D. Power low retail','J.D. Power average retail','Seller-confirmed price'],y=[124600,150150,155000],marker_color=['#708f88','#9ed4bc','#e5bd79'],text=['$124,600','$150,150','$155,000'],textposition='outside'))
    fig.update_layout(yaxis_title='US dollars',showlegend=False,yaxis_range=[0,190000])
    return html.Div([html.H2('Is this Atlas a compelling deal?'),html.P('2020 Atlas Murphy Suite Tommy Bahama · approximately 15,243 miles · Newcastle, Maine.',className='sub'),
      html.Div([metric('Seller-confirmed price','$155,000','Buyer-reported direct quote, not signed transaction'),metric('J.D. Power average retail','$150,150','Published guide benchmark, not a vehicle appraisal'),metric('Premium to guide average','3.2%','($155,000 / $150,150 − 1) × 100')],className='grid'),
      panel(dcc.Graph(figure=figure_style(fig)),html.P('These guide figures do not reflect the exact condition or specific upgrades of the vehicle. Comparable advertised prices and completed sales must be distinguished.',className='note')),
      panel(html.H3('What would change our assessment?'),html.P('Obtain documented Mercedes and Airstream service invoices, tire dates, generator hours, title/lien status, independent inspections, and a broader sample of closely matched active listings. Do not assign resale value to undocumented upgrades.'),html.A('J.D. Power valuation source',href='https://www.jdpower.com/rvs/2020/airstream/murphy-suite-tommy-bahama/6594205/values',target='_blank'))])

def route():
    stops=['Northern Maine','New Brunswick','Nova Scotia / PEI','Québec','Northern Vermont / Upstate NY','Ohio / Airstream service','Mackinac area','Wisconsin / Minnesota','New Orleans','Texas','New Mexico / Colorado','Wyoming / Montana','Calgary / Edmonton','Idaho / Washington','Pacific Coast','Lake Tahoe / Las Vegas']
    return html.Div([html.H2('Travel as a housing strategy'),html.P('A conceptual corridor, not a fixed itinerary or a validated mileage estimate.',className='sub'),panel(html.Div([html.Div(f'{i+1:02d}  {s}',style={'padding':'11px 14px','borderBottom':'1px solid #2b3b3d'}) for i,s in enumerate(stops)])),panel(html.H3('Stay mix: the research hypothesis'),html.P('Longer stays, hosted overnight stops, friends and family, and occasional campgrounds may reduce site costs. These options must be checked for legal overnight use, seasonal availability, membership obligations, and access to utilities.'),html.P('Costco lots are not assumed to permit overnight stays. Canadian border, insurance and remote-work restrictions need separate verification.',className='note'))])

def methods():
    links=[('Census historical household income / age H-10','https://www.census.gov/data/tables/time-series/demo/income-poverty/historical-income-households.html'),('FRED official time series','https://fred.stlouisfed.org/'),('FHFA house price index','https://www.fhfa.gov/data/hpi'),('J.D. Power Atlas values','https://www.jdpower.com/rvs/2020/airstream/murphy-suite-tommy-bahama/6594205/values'),('Original vehicle listing','https://www.airstreammarketplace.com/airstream-trailers-for-sale/2020-24-atlas-for-sale-in-newcastle-maine/')]
    return html.Div([html.H2('Sources and research integrity'),panel(html.H3('Source register'),html.Ul([html.Li(html.A(label,href=url,target='_blank')) for label,url in links])),panel(html.H3('Evidence levels'),html.P('Observed: official time-series data, published guide values. Buyer-reported: seller quote, vehicle tour and service claims. Assumed: financing APR, future site costs, fuel, depreciation and resale.'),html.P('Data must be fetched using python refresh_data.py. Missing series remain visibly unavailable, never replaced with invented historical observations.'),html.P('Limitations: guide values are not transaction prices; household aggregates do not isolate 31-year-olds; site budgets are scenarios, not observed future bookings; ownership cost excludes personal taxes and any tow-car decision until modeled.'))])

app.layout=html.Div([html.Div('APPLIED ECONOMICS / RESEARCH DASHBOARD',className='eyebrow'),html.H1('The Economics of Mobility',className='hero'),html.P('A generation apart. One housing decision. A transparent analysis of affordability, geographic freedom, and a $155,000 Airstream Atlas.',className='sub'),
html.Div([metric('Current monthly rent','$3,000','Excludes utilities'),metric('Atlas purchase price','$155,000','Seller-confirmed during tour'),metric('Research horizon','1990–2026','Spring 2028 departure target')],className='grid'),
dcc.Tabs(id='tabs',value='housing',className='tabs',children=[dcc.Tab(label='Housing scenarios',value='housing'),dcc.Tab(label='Historical economics',value='history'),dcc.Tab(label='Atlas valuation',value='valuation'),dcc.Tab(label='Route economics',value='route'),dcc.Tab(label='Methodology',value='methods')]),html.Div(id='page'),html.P('Research prototype · November 2026 · All figures nominal USD unless labeled otherwise.',className='small')],className='wrap')
@app.callback(Output('page','children'),Input('tabs','value'))
def page(tab):return {'housing':housing,'history':historical,'valuation':valuation,'route':route,'methods':methods}[tab]()
@app.callback(Output('history-chart','figure'),Output('history-source','children'),Input('series','value'))
def history_chart(series):
    df=load(series,str(BASE/'data/raw'))
    fig=go.Figure()
    if df is None:
        fig.add_annotation(text='Data not downloaded yet. Run: python refresh_data.py',showarrow=False,font=dict(size=17,color='#e5bd79'))
        fig.update_xaxes(visible=False);fig.update_yaxes(visible=False)
        return figure_style(fig),f'{series}: official series not yet retrieved. No observations fabricated.'
    df=df[df.date.dt.year>=1985]
    fig.add_trace(go.Scatter(x=df.date,y=df.value,mode='lines',line=dict(color='#9ed4bc',width=3),name=series))
    return figure_style(fig),f'{series} · {SERIES[series]} · {len(df):,} observations · {df.date.min().date()} through {df.date.max().date()} · source: FRED / originating agency.'
@app.callback(Output('scenario-metrics','children'),Output('housing-chart','figure'),Output('scenario-comment','children'),*[Input(k,'value') for k in ['rate','years','campsite','diesel','other','resale','upfront']])
def update(rate,years,campsite,diesel,other,resale,upfront):
    v=scenario(rate=rate,years=years,campsite=campsite,diesel=diesel,other=other,resale_pct=resale,upfront=upfront)
    cash=v['monthly_cash_difference'];net=v['net_difference']
    stats=html.Div([html.Div(f"Monthly Atlas cash outflow: ${v['monthly']:,.0f}"),html.Div(f"Monthly difference vs rent: ${cash:+,.0f}"),html.Div(f"3-year Atlas net economic cost: ${v['net_cost']:,.0f}"),html.Div(f"3-year rent cost: ${v['rent_cost']:,.0f}"),html.Div(f"Loan balance after 3 years: ${v['balance']:,.0f}")],style={'lineHeight':'2'})
    fig=go.Figure(go.Bar(x=['Rent: 3 years','Atlas: 3 years'],y=[v['rent_cost'],v['net_cost']],marker_color=['#9aa9a3','#9ed4bc'],text=[f"${v['rent_cost']:,.0f}",f"${v['net_cost']:,.0f}"],textposition='outside'))
    fig.update_layout(showlegend=False,yaxis_title='Net nominal cost (USD)')
    msg=f"Under these assumptions, Atlas net ownership cost is ${abs(net):,.0f} {'lower' if net>=0 else 'higher'} than rent over 36 months. The resale percentage is a scenario, not a market forecast."
    return stats,figure_style(fig),msg
if __name__=='__main__':app.run(debug=True)
