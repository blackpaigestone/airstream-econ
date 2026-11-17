from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from src.model import scenario
from src.optionality import flexibility_cost, five_year_outcome, opportunity_value, income_gain_value
from src.data_sources import SERIES,load
from src.research.historical import build_historical_panel
from src.research.households import household_budget, readiness_budget
from src.research.household_evidence import load_evidence
from src.research.census_acs import load_panel
from src.research.census_income import load_income_panel, real_income_index
from src.research.census_rent_burden import load_burden_panel
from src.research.household_microdata import load_households, summarize_renter_burden

BASE=Path(__file__).parent
app=Dash(__name__,title='The Economics of Optionality')
server=app.server
COLORS={'ink':'#e8eee9','muted':'#9aa9a3','bg':'#0e1719','panel':'#182528','accent':'#9ed4bc','gold':'#e5bd79'}
app.index_string='''<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}<style>
body{margin:0;background:#0e1719;color:#e8eee9;font-family:Inter,Arial,sans-serif} .wrap{max-width:1220px;margin:auto;padding:30px 22px 80px}.eyebrow{letter-spacing:3px;color:#9ed4bc;font-size:12px;font-weight:700}.hero{font-size:clamp(36px,5vw,66px);letter-spacing:-2px;margin:14px 0 10px}.sub{color:#9aa9a3;line-height:1.6;max-width:850px}.panel{background:#182528;border:1px solid #2b3b3d;border-radius:18px;padding:22px;margin:16px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:15px}.metric{font-size:29px;font-weight:700;margin:9px 0;color:#e8eee9}.small{font-size:12px;color:#9aa9a3;line-height:1.6}.label{color:#9ed4bc;font-size:12px;letter-spacing:1px;text-transform:uppercase}.tabs{margin:28px 0}.dash-tab{background:#182528!important;color:#c4d0ca!important;border:0!important}.dash-tab--selected{border-bottom:3px solid #9ed4bc!important;color:white!important}.control{padding:12px 0}.control label{display:block;margin-bottom:8px;color:#d5dfd9;font-size:13px}h2{font-size:28px;margin:0 0 12px}a{color:#9ed4bc} .note{padding:14px;border-left:3px solid #e5bd79;background:#26302c;line-height:1.6}input{color:#0e1719} @media(max-width:600px){.wrap{padding:20px 12px}}
</style></head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>'''
def panel(*children):return html.Div(children,className='panel')
def metric(name,value,note):return html.Div([html.Div(name,className='label'),html.Div(value,className='metric'),html.Div(note,className='small')],className='panel')
def figure_style(fig):
    fig.update_layout(paper_bgcolor='#182528',plot_bgcolor='#182528',font_color='#e8eee9',margin=dict(l=35,r=20,t=55,b=55),legend=dict(orientation='h',y=-.25),hovermode='x unified')
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


# Research extension: observed macro comparisons + explicitly hypothetical option scenarios.
def systems_research():
    return html.Div([
      html.H2('The economic value of income growth'),
      html.P('Research question 1: Does an equal real income gain translate into equal progress toward financial independence? The observed lines below describe national series; the household calculator is illustrative, not a historical estimate.',className='sub'),
      panel(html.H3('Observed CPI and real household income — indexed separately'),dcc.Graph(id='systems-chart'),html.Div(id='systems-note',className='small')),
      panel(html.H3('Illustrative income-gain transmission'),html.P('Compare the impact of an identical annual income gain under different essential-spending and asset-entry conditions.'),
        html.Div([html.Label('Annual take-home income ($)'),dcc.Slider(id='sys-income',min=35000,max=150000,step=5000,value=75000,tooltip={'always_visible':True}),
                  html.Label('Essential expenditure share (%)'),dcc.Slider(id='sys-essential',min=35,max=95,step=5,value=75,tooltip={'always_visible':True}),
                  html.Label('Additional annual real income ($)'),dcc.Slider(id='sys-gain',min=1000,max=15000,step=1000,value=5000,tooltip={'always_visible':True}),
                  html.Label('Asset entry cash requirement ($)'),dcc.Slider(id='sys-target',min=10000,max=150000,step=5000,value=60000,tooltip={'always_visible':True})],className='control'),
        html.Div(id='systems-result'),html.P('Assumes expenses do not change when income rises, a fixed target, zero initial savings and zero investment returns. These are user-selected scenarios.',className='small')),
      panel(html.H3('Identification limits'),html.P('National median income is not a matched panel of 31-year-old single renters. The CPI index and real income are indexed for visualization, not divided into one another. Age/household-specific BLS CE and Census data are required before making historical claims about single-person budgets.',className='note'))])

def flexibility_research():
    return html.Div([html.H2('The cost and value of financial flexibility'),html.P('Research question 2: Has the cost of maintaining a comparable set of choices increased relative to earnings? Here we define an explicit reference basket and test its sensitivity. Historical index construction remains pending primary-source data.',className='sub'),
      panel(html.H3('Reference flexibility basket — illustrative annual costs'),
       html.Label('Monthly essential costs ($)'),dcc.Slider(id='flex-essential',min=1000,max=6000,step=250,value=3000,tooltip={'always_visible':True}),
       html.Label('Emergency runway (months)'),dcc.Slider(id='flex-runway',min=3,max=12,step=1,value=6,tooltip={'always_visible':True}),
       html.Label('Relocation / transition reserve ($)'),dcc.Slider(id='flex-move',min=2000,max=25000,step=1000,value=10000,tooltip={'always_visible':True}),
       html.Label('Annual after-tax income ($)'),dcc.Slider(id='flex-income',min=35000,max=150000,step=5000,value=75000,tooltip={'always_visible':True}),html.Div(id='flex-result')),
      panel(html.H3('What a historical flexibility index requires'),html.P('Historical relocation and lease-exit costs, liquid assets by age/household type, regional housing costs, job opportunity geography, and comparable household incomes. We will not substitute CPI for the price of flexibility: it is a different basket.',className='note'))])

def choice_research():
    return html.Div([html.H2('Mobility, ownership and the five-year option set'),html.P('Research question 3: When does asset ownership outweigh the opportunity costs of geographic commitment? The Atlas is a depreciating vehicle, not a home-equity substitute. Compare liquid wealth, net wealth and ability to act on future opportunities.',className='sub'),
      panel(html.H3('Five-year strategy — editable assumptions'),html.P('Remote field employment funds the baseline; an artist-representation business is a separate uncertain income stream, defaulted to zero rather than presumed profitable.'),
       html.Label('Monthly net remote employment income ($)'),dcc.Slider(id='choice-job',min=2500,max=12000,step=250,value=6500,tooltip={'always_visible':True}),
       html.Label('Monthly net business contribution ($)'),dcc.Slider(id='choice-business',min=-1000,max=4000,step=250,value=0,tooltip={'always_visible':True}),
       html.Label('Atlas operating expenses beyond loan ($/month)'),dcc.Slider(id='choice-operating',min=500,max=4500,step=100,value=1500,tooltip={'always_visible':True}),
       html.Label('Atlas resale value after 5 years (% of purchase price)'),dcc.Slider(id='choice-resale',min=25,max=100,step=5,value=60,tooltip={'always_visible':True}),
       html.Label('Starting liquid savings ($)'),dcc.Slider(id='choice-start',min=0,max=100000,step=5000,value=5000,tooltip={'always_visible':True}),
       html.Div(id='choice-results'),dcc.Graph(id='choice-chart')),
      panel(html.H3('Geographic opportunity exercise'),html.P('Illustrative expected benefit of an opportunity, net of relocation costs and foregone alternatives. Compare stationary and mobile strategies.'),
       html.Label('Opportunity benefit ($)'),dcc.Slider(id='choice-benefit',min=0,max=75000,step=2500,value=25000,tooltip={'always_visible':True}),
       html.Label('Stationary transition cost ($)'),dcc.Slider(id='choice-fixedcost',min=0,max=40000,step=1000,value=15000,tooltip={'always_visible':True}),
       html.Label('Mobile transition cost ($)'),dcc.Slider(id='choice-mobilecost',min=0,max=40000,step=1000,value=5000,tooltip={'always_visible':True}),
       html.Div(id='choice-opportunity'),html.P('Excludes probability of an offer, local labor market access, visa/work authorization, insurance, taxation, and employment restrictions. This is not a causal estimate of the value of mobility.',className='small'))])

def indexed_chart():
    fig=go.Figure(); details=[]
    for key,name,color in [('CPIAUCSL','CPI (price level)','#e5bd79'),('MEHOINUSA672N','Real median household income','#9ed4bc')]:
        df=load(key,str(BASE/'data/raw'))
        if df is None: details.append(f'{key} missing — run python refresh_data.py');continue
        df=df[(df.date.dt.year>=1990)&(df.date.dt.year<=2025)].copy()
        df=df.groupby(df.date.dt.year,as_index=False).agg({'value':'mean','date':'min'})
        base=df.loc[df.date.dt.year==1990,'value']
        if base.empty: details.append(f'{key} missing 1990 baseline');continue
        fig.add_trace(go.Scatter(x=df.date.dt.year,y=100*df.value/base.iloc[0],name=name,mode='lines',line=dict(color=color,width=3)))
        details.append(f'{key}: 1990=100; annual mean of observed values; through {int(df.date.dt.year.max())}')
    if not fig.data: fig.add_annotation(text='Observed series unavailable. Run python refresh_data.py',showarrow=False)
    fig.update_layout(yaxis_title='Index, 1990=100',xaxis_title='Year')
    return figure_style(fig),' | '.join(details)

def historical_evidence():
    return html.Div([
      html.H2('Historical evidence · national benchmarks'),
      html.P('Research questions: income value, flexibility, and ownership versus mobility. These first charts describe national aggregates; they do not isolate younger single-income renters or measure the value of financial options.',className='sub'),
      panel(html.H3('Observed income and inflation-adjusted home prices'),dcc.Graph(id='evidence-levels'),html.Div(id='evidence-coverage',className='small')),
      panel(html.H3('Relative housing acquisition burdens'),dcc.Graph(id='evidence-burdens'),html.P('1990=100. A value of 150 indicates a 50% increase relative to the 1990 benchmark, not a 150% share of income.',className='small')),
      panel(html.H3('Research integrity'),html.P('Real median household income is already adjusted for inflation; we do not deflate it again. New-home median sale prices reflect changing composition; FHFA measures a different housing concept. Mortgage-payment burden is a standardized proxy, not actual household underwriting.',className='note'),html.P('This release does not establish the historical value of flexibility, causal effects, or young single-income household outcomes. See RESEARCH_V3.md for definitions and next data requirements.'))])

@app.callback(Output('evidence-levels','figure'),Output('evidence-burdens','figure'),Output('evidence-coverage','children'),Input('tabs','value'))
def evidence_charts(_):
    a=go.Figure();b=go.Figure()
    try:
        data=build_historical_panel(BASE/'data/raw',base_year=1990)
    except (FileNotFoundError,ValueError) as exc:
        for fig in (a,b):
            fig.add_annotation(text='Historical data unavailable — check local FRED CSVs',showarrow=False)
        return figure_style(a),figure_style(b),str(exc)
    for col,label,color in [('real_income_index','Real median household income','#9ed4bc'),('real_new_home_price_index','Real median NEW home sale price','#e5bd79'),('real_fhfa_index','Real FHFA house price index','#92a7e2')]:
        a.add_trace(go.Scatter(x=data.year,y=data[col],mode='lines',name=label,line=dict(color=color,width=3)))
    for col,label,color in [('new_home_price_to_income_index','New-home price / real income (relative)','#e5bd79'),('mortgage_payment_to_income_index','Standardized mortgage payment / real income (relative)','#9ed4bc')]:
        b.add_trace(go.Scatter(x=data.year,y=data[col],mode='lines',name=label,line=dict(color=color,width=3)))
    for fig in (a,b):
        fig.update_layout(xaxis_title='Calendar year',yaxis_title='Index (1990=100)')
    return figure_style(a),figure_style(b),f'Observed common-year coverage: {int(data.year.min())}–{int(data.year.max())}, {len(data)} annual observations. Sources: FRED / Census / BLS / FHFA / Freddie Mac. Annual means for nonannual series. No fabricated data.'

def household_research():
    return html.Div([
      html.H2('Household scale & financial readiness · V4'),
      html.P('RQ4: Has the age at which independent economic stability becomes feasible shifted? This tab introduces a transparent scenario model. It is NOT an observed historical age comparison.',className='sub'),
      panel(html.H3('Economies of sharing a household'),
        html.P('Hold household fixed expenses constant to isolate sharing economies. Vary earners independently to separate cost-sharing from additional income.'),
        html.Label('Adults in household'),dcc.Slider(id='hh-adults',min=1,max=5,step=1,value=1,marks={i:str(i) for i in range(1,6)}),
        html.Label('Number of income earners'),dcc.Slider(id='hh-earners',min=0,max=5,step=1,value=1,marks={i:str(i) for i in range(6)}),
        html.Label('Fixed shared costs ($/month)'),dcc.Slider(id='hh-fixed',min=500,max=5000,step=100,value=2000,tooltip={'always_visible':True}),
        html.Label('Variable costs per adult ($/month)'),dcc.Slider(id='hh-variable',min=200,max=2000,step=50,value=600,tooltip={'always_visible':True}),
        html.Label('Net monthly income per earner ($)'),dcc.Slider(id='hh-wage',min=0,max=12000,step=250,value=4000,tooltip={'always_visible':True}),
        html.Div(id='hh-summary'),dcc.Graph(id='hh-scale-chart'),
        html.P('Hypothetical budget only. Actual housing requirements, taxes, dependent costs, and household economies are heterogeneous. Cost sharing is not the same as having more earners.',className='small')),
      panel(html.H3('Financial independence readiness · scenario'),
        html.P('Readiness is operationalized as positive cash flow, a minimum savings rate, and liquid reserves sufficient for emergencies plus a transition. It is not a measure of personal maturity.'),
        html.Label('Liquid savings ($)'),dcc.Slider(id='hh-savings',min=0,max=100000,step=1000,value=10000,tooltip={'always_visible':True}),
        html.Label('Emergency reserve (months)'),dcc.Slider(id='hh-runway',min=0,max=12,step=1,value=3,marks={i:str(i) for i in (0,3,6,9,12)}),
        html.Label('Relocation / opportunity fund ($)'),dcc.Slider(id='hh-transition',min=0,max=30000,step=1000,value=5000,tooltip={'always_visible':True}),
        html.Label('Minimum sustainable savings rate (%)'),dcc.Slider(id='hh-minrate',min=0,max=30,step=5,value=10,marks={i:f'{i}%' for i in (0,10,20,30)}),
        html.Div(id='hh-readiness')),
      panel(html.H3('Historical readiness: evidence still required'),
        html.P('Primary published age band: 25–34; comparison groups: 35–44 and 45–54. A readiness-age curve requires consistently defined age-specific microdata with liquid savings, income, and household expenses. No age-gap estimates are plotted without those observations.',className='note'),
        html.P('V4 includes a validated, unweighted microdata calculation function in src/research/households.py. Before publishing historical estimates, obtain documented source data, survey weights, harmonized definitions and coverage checks. See RESEARCH_V4.md.'))])

@app.callback(Output('hh-summary','children'),Output('hh-scale-chart','figure'),Output('hh-readiness','children'),
              Input('hh-adults','value'),Input('hh-earners','value'),Input('hh-fixed','value'),Input('hh-variable','value'),Input('hh-wage','value'),
              Input('hh-savings','value'),Input('hh-runway','value'),Input('hh-transition','value'),Input('hh-minrate','value'))
def household_outputs(adults,earners,fixed,variable,wage,savings,runway,transition,minrate):
    earners=min(earners,adults)
    b=household_budget(adults,earners,fixed,variable,wage)
    r=readiness_budget(b['income'],b['expenses'],savings,runway,transition,minrate/100)
    fig=go.Figure()
    xs=list(range(1,6))
    fig.add_trace(go.Bar(x=xs,y=[household_budget(n,min(earners,n),fixed,variable,wage)['per_adult_cost'] for n in xs],name='Cost per adult',marker_color='#9ed4bc'))
    fig.update_layout(xaxis_title='Adults sharing expenses',yaxis_title='Monthly cost per adult ($)',xaxis=dict(tickmode='array',tickvals=xs))
    summary=html.Div([html.P(f'Household monthly costs: ${b["expenses"]:,.0f} | Per adult: ${b["per_adult_cost"]:,.0f} | Net household income: ${b["income"]:,.0f} | Monthly surplus: ${b["surplus"]:,.0f}'),
                      html.P(f'Income earners used: {earners} of {adults}. Bar chart holds fixed and per-adult variable costs constant; no observed population data.',className='small')])
    months='not reachable with current surplus' if r['months_to_reserve'] is None else f'{r["months_to_reserve"]:.1f} months'
    ready='MEETS the selected scenario thresholds' if r['fully_ready'] else 'DOES NOT meet all selected scenario thresholds'
    readiness=html.Div([html.P(f'Reserve + transition target: ${r["reserve_target"]:,.0f} | Available liquid savings: ${savings:,.0f}'),
                        html.P(f'Scenario status: {ready}'),html.P(f'Estimated time to target at constant surplus: {months}. This is a deterministic scenario, not a forecast.',className='small')])
    return summary,figure_style(fig),readiness

def household_evidence():
    return html.Div([html.H2('Historical household evidence'),
      html.P('Survey-weighted descriptive results from a documented, harmonized household extract. No data are synthesized or downloaded automatically.',className='sub'),
      panel(html.H3('Population and indicator'),
        html.Label('Age bracket'),dcc.Dropdown(id='hh-ev-age',options=[{'label':v,'value':v} for v in ['25–34','35–44','45–54']],value='25–34',style={'color':'#172022'}),
        html.Label('Population'),dcc.Dropdown(id='hh-ev-group',options=[{'label':v,'value':v} for v in ['all households','solo adult renter','shared adult renter']],value='all households',style={'color':'#172022'}),
        html.Label('Measure'),dcc.Dropdown(id='hh-ev-metric',options=[{'label':v,'value':k} for k,v in [('readiness_share','Readiness share (proxy)'),('positive_cashflow_share','Nonnegative cashflow share'),('weighted_savings_capacity','Annual disposable income minus essential spending'),('weighted_per_adult_essentials','Annual essentials per adult'),('weighted_independent_premium','Solo/shared observed spending ratio')]],value='readiness_share',style={'color':'#172022'}),
        dcc.Graph(id='hh-ev-chart'),html.Div(id='hh-ev-coverage',className='small')),
      panel(html.H3('Evidence boundary'),html.P('The required file is data/external/household_harmonized.csv. This is a researcher-produced harmonized extract, NOT a raw SCF, CE or Census file. Each source must document sample universe, survey weights, financial definitions, price base and comparability. No cross-source pooling, imputation, or readiness-age gap is inferred.'),
        html.P('A solo/shared spending ratio describes observed groups; it does not identify the causal effect of sharing a household. Financial readiness is an operational proxy, not a validated financial-health diagnosis.',className='note')),
      panel(html.H3('Observed Census tenure by age of householder'),
        html.P('US Census ACS 1-year, table B25007. These are observed housing tenure estimates for households classified by the age of the householder—not income, spending, financial readiness, or solo/shared household status.',className='small'),
        html.P('All three age brackets appear together; 25–34 is highlighted as the primary cohort.',className='small'),
        html.Label('Tenure measure'),dcc.Dropdown(id='acs-measure',options=[{'label':'Renter share','value':'renter_share'},{'label':'Owner share','value':'owner_share'},{'label':'Renter households','value':'renter_households'},{'label':'Owner households','value':'owner_households'}],value='renter_share',style={'color':'#172022'}),
        dcc.Graph(id='acs-chart'),html.Div(id='acs-coverage',className='small')),
      panel(html.H3('Observed Census median household income by age'),
        html.P('ACS 1-year B19049 published income age bands: Under 25, 25–44, 45–64, 65+. These DIFFER from the 25–34, 35–44, 45–54 housing tenure bands. Medians are household-level, not individual earnings. Annual CPI converts survey-year dollars to a comparable real-income index. No missing years are interpolated.',className='small'),
        html.Label('Income measure'),dcc.Dropdown(id='acs-income-measure',options=[{'label':'Median household income (survey-year dollars)','value':'nominal'},{'label':'Real income index (2010=100)','value':'real_index'}],value='real_index',style={'color':'#172022'}),
        dcc.Graph(id='acs-income-chart'),html.Div(id='acs-income-coverage',className='small')),
      panel(html.H3('National renter housing-cost burden · V5.3'),
        html.P('Observed ACS 1-year B25070. Share of renter households spending at least 30% or 50% of household income on gross rent (rent plus applicable utilities). Denominator excludes households for which the ratio is not computed. These observations cover ALL ages and cannot be attributed to the 25–34 cohort.',className='small'),
        dcc.Graph(id='acs-burden-chart'),html.Div(id='acs-burden-coverage',className='small'),
        html.P('Cost burden is a descriptive affordability indicator, not disposable income, a readiness score, or evidence that sharing housing causes a particular outcome. No direct age-specific income-to-burden comparison is made.',className='note')),
      panel(html.H3('Household-level renter affordability · V5.4'),
        html.P('Prepared household-level microdata only. This section remains unavailable until a source-verified extract is supplied. One-person versus multi-person households are descriptive groups, not a causal sharing effect.',className='small'),
        html.Label('Age of householder'),dcc.Dropdown(id='micro-age',options=[{'label':a,'value':a} for a in ['25–34','35–44','45–54']],value='25–34',style={'color':'#172022'}),
        html.Label('Housing burden threshold'),dcc.Dropdown(id='micro-threshold',options=[{'label':'At least 30%','value':'burden_30_share'},{'label':'At least 50%','value':'burden_50_share'}],value='burden_30_share',style={'color':'#172022'}),
        dcc.Graph(id='micro-chart'),html.Div(id='micro-coverage',className='small'),
        html.P('Survey weights are applied to household shares. Cells with fewer than 30 valid unweighted households are suppressed. Design-based uncertainty intervals are not yet available. Do not infer an age of financial independence.',className='note'))])

AGE_COLORS={'25–34':'#66d4b3','35–44':'#72a8f7','45–54':'#f2b66d'}
INCOME_COLORS={'Under 25':'#b8a6ed','25–44':'#66d4b3','45–64':'#f2b66d','65+':'#72a8f7'}

def age_comparison_figure(d, measure, title, *, share=False, indexed=False, colors=None):
    """Display all standard age bands; do not connect missing survey years."""
    fig=go.Figure()
    for age,color in (colors or AGE_COLORS).items():
        sub=d.loc[d.age_band.eq(age)].sort_values('year')
        if sub.empty:
            continue
        years=range(int(sub.year.min()),int(sub.year.max())+1)
        vals=sub.set_index('year')[measure].reindex(years)
        fig.add_trace(go.Scatter(x=list(years),y=vals,mode='lines+markers',name=age,
            line={'color':color,'width':3 if age in ('25–34','25–44') else 2},
            marker={'size':7 if age in ('25–34','25–44') else 5},connectgaps=False,
            hovertemplate=f'Age {age}<br>Year %{{x}}<br>Value %{{y:{".1%" if share else ",.1f"}}}<extra></extra>'))
    if share: fig.update_yaxes(tickformat='.0%',range=[0,1])
    if indexed: fig.update_yaxes(title='Index (2010=100)')
    fig.update_layout(title=title,legend={'orientation':'h','y':1.14,'x':0})
    return figure_style(fig)

@app.callback(Output('acs-chart','figure'),Output('acs-coverage','children'),Input('acs-measure','value'))
def acs_chart(measure):
    fig=go.Figure()
    try:
        d=load_panel(BASE/'data/external/census_acs_tenure_age.csv')
    except (FileNotFoundError,ValueError) as exc:
        fig.add_annotation(text='Census ACS observations not downloaded yet',showarrow=False,font={'size':17})
        return figure_style(fig),f'{exc}. Run python refresh_household_data.py.'
    if measure not in ('renter_share','owner_share','renter_households','owner_households'):
        fig.add_annotation(text='Unsupported Census measure',showarrow=False)
        return figure_style(fig),'No data for selection.'
    fig=age_comparison_figure(d,measure,f'{measure.replace("_"," ").title()} · age of householder',share=measure.endswith('_share'))
    years=set(d.year.astype(int)); gaps=sorted(set(range(min(years),max(years)+1))-years)
    note=f'Official ACS 1-year B25007 estimates · {len(years)} years · {min(years)}–{max(years)}. Missing years: {gaps}. No interpolation; not a financial-readiness measure.'
    return fig,note

@app.callback(Output('acs-income-chart','figure'),Output('acs-income-coverage','children'),Input('acs-income-measure','value'))
def acs_income_chart(measure):
    fig=go.Figure()
    try:
        d=load_income_panel(BASE/'data/external/census_acs_income_age.csv')
        if measure=='real_index':
            d=real_income_index(d,BASE/'data/raw/CPIAUCSL.csv',base_year=2010)
            col='real_income_index'
        elif measure=='nominal': col='median_household_income'
        else: raise ValueError('Unsupported income measure')
    except (FileNotFoundError,ValueError,KeyError) as exc:
        fig.add_annotation(text='ACS income observations or CPI data unavailable',showarrow=False,font={'size':16})
        return figure_style(fig),f'{exc}. Run python refresh_household_income.py. Real-income index additionally requires data/raw/CPIAUCSL.csv.'
    fig=age_comparison_figure(d,col,'Median household income · published B19049 age groups · '+('real index (2010=100)' if measure=='real_index' else 'survey-year USD'),indexed=measure=='real_index',colors=INCOME_COLORS)
    years=set(d.year.astype(int));gaps=sorted(set(range(min(years),max(years)+1))-years)
    return fig,f'Official ACS 1-year B19049 · {len(years)} years, {min(years)}–{max(years)}; missing: {gaps}. B19049 age groups: Under 25, 25–44, 45–64, 65+ (not the narrower tenure age groups). Household medians, not individual wages, disposable income, or financial readiness. No interpolation.'

@app.callback(Output('acs-burden-chart','figure'),Output('acs-burden-coverage','children'),Input('tabs','value'))
def acs_burden_chart(_):
    fig=go.Figure()
    try:
        d=load_burden_panel(BASE/'data/external/census_acs_rent_burden.csv')
    except (FileNotFoundError,ValueError) as exc:
        fig.add_annotation(text='National renter burden data not downloaded yet',showarrow=False,font={'size':16})
        return figure_style(fig),f'{exc}. Run python refresh_rent_burden.py.'
    years=range(int(d.year.min()),int(d.year.max())+1)
    for col,label,color in [('burden_30_share','At least 30%','#66d4b3'),('burden_50_share','At least 50%','#f2b66d')]:
        vals=d.set_index('year')[col].reindex(years)
        fig.add_trace(go.Scatter(x=list(years),y=vals,mode='lines+markers',name=label,
            line={'color':color,'width':3},connectgaps=False,
            hovertemplate=label+'<br>Year %{x}<br>Share %{y:.1%}<extra></extra>'))
    fig.update_layout(legend={'orientation':'h','y':1.1,'x':0},hovermode='x unified')
    fig.update_yaxes(tickformat='.0%',rangemode='tozero',title='Share of renter households (computed cases)')
    fig.update_xaxes(title='ACS survey year',dtick=2)
    gaps=sorted(set(years)-set(d.year.astype(int)))
    return figure_style(fig),f'Official ACS 1-year B25070 · {len(d)} years, {min(years)}–{max(years)}; missing: {gaps}. US renter households, all ages. Denominator excludes B25070 not-computed cases. No interpolation.'

@app.callback(Output('micro-chart','figure'),Output('micro-coverage','children'),
              Input('micro-age','value'),Input('micro-threshold','value'))
def micro_chart(age,threshold):
    fig=go.Figure()
    try:
        d=summarize_renter_burden(load_households(BASE/'data/external/household_microdata_prepared.csv'))
    except (FileNotFoundError,ValueError) as exc:
        fig.add_annotation(text='Verified household-level observations not yet available',showarrow=False,font={'size':15})
        return figure_style(fig),f'{exc}. See RESEARCH_V5_4.md and the prepared extract schema.'
    d=d[d.age_band==age]
    if d.empty:
        fig.add_annotation(text='No eligible survey cells (n >= 30)',showarrow=False)
        return figure_style(fig),'No eligible cells for this age bracket.'
    years=list(range(int(d.year.min()),int(d.year.max())+1))
    for (source,kind),g in d.groupby(['source_id','household_type']):
        g=g.set_index('year').reindex(years)
        fig.add_trace(go.Scatter(x=years,y=g[threshold],mode='lines+markers',connectgaps=False,
          name=f'{kind} · {source}',line={'color':'#66d4b3' if kind=='one-person' else '#f2b66d',
          'dash':'solid' if kind=='one-person' else 'dash'},
          hovertemplate='Year %{x}<br>Burden %{y:.1%}<extra>%{fullData.name}</extra>'))
    fig.update_layout(title=f'{age} · weighted renter cost burden · prepared household microdata')
    fig.update_yaxes(tickformat='.0%',range=[0,1],title='Share of renter households')
    return figure_style(fig),f'{len(d)} eligible source-year-group cells. Weighted household shares; minimum 30 unweighted valid observations per cell. No design-based confidence intervals or causal claims.'

@app.callback(Output('hh-ev-chart','figure'),Output('hh-ev-coverage','children'),
              Input('hh-ev-age','value'),Input('hh-ev-group','value'),Input('hh-ev-metric','value'))
def household_evidence_chart(age,group,metric):
    fig=go.Figure()
    try:
        d=load_evidence(BASE/'data/external/household_harmonized.csv')
    except (FileNotFoundError,ValueError) as exc:
        fig.add_annotation(text='Historical household observations unavailable',showarrow=False,font={'size':17})
        return figure_style(fig),f'{exc}. See RESEARCH_V5.md for schema and provenance requirements.'
    d=d[(d.age_band==age)&(d.group==group)].sort_values('year')
    if d.empty or metric not in d.columns or d[metric].notna().sum()==0:
        fig.add_annotation(text='No eligible observations for selection',showarrow=False)
        return figure_style(fig),'No qualifying survey cells; minimum sample is 30 unweighted households per source/year/age/population.'
    for source,p in d.groupby('source_id'):
        fig.add_trace(go.Scatter(x=p.year,y=p[metric],mode='lines+markers',name=source,customdata=p[['n']],hovertemplate='Year %{x}<br>Value %{y:.3f}<br>Unweighted n %{customdata[0]}<extra>%{fullData.name}</extra>'))
    if metric in ('readiness_share','positive_cashflow_share'):
        fig.update_yaxes(tickformat='.0%',range=[0,1])
    fig.update_layout(title=f'{age} · {group} · {metric} (observed harmonized extract)')
    return figure_style(fig),f'{len(d)} source-year cells; {int(d.n.sum())} unweighted household records across cells. Each series is source-specific; no interpolation or pooling.'

app.layout=html.Div([html.Div('APPLIED ECONOMICS / RESEARCH DASHBOARD',className='eyebrow'),html.H1('The Economics of Optionality',className='hero'),html.P('A generation apart. One housing decision. A transparent analysis of affordability, geographic freedom, and a $155,000 Airstream Atlas.',className='sub'),
html.Div([metric('Current monthly rent','$3,000','Excludes utilities'),metric('Atlas purchase price','$155,000','Seller-confirmed during tour'),metric('Research horizon','1990–2026','Spring 2028 departure target')],className='grid'),
dcc.Tabs(id='tabs',value='housing',className='tabs',children=[dcc.Tab(label='Housing scenarios',value='housing'),dcc.Tab(label='Historical economics',value='history'),dcc.Tab(label='Atlas valuation',value='valuation'),dcc.Tab(label='Route economics',value='route'),dcc.Tab(label='Historical evidence',value='evidence'),dcc.Tab(label='Household readiness',value='households'),dcc.Tab(label='Household evidence',value='hh-evidence'),dcc.Tab(label='Income value',value='systems'),dcc.Tab(label='Flexibility',value='flexibility'),dcc.Tab(label='Five-year choices',value='choices'),dcc.Tab(label='Methodology',value='methods')]),
html.Div([html.Div(housing(),id='page-housing'),html.Div(historical(),id='page-history',style={'display':'none'}),html.Div(valuation(),id='page-valuation',style={'display':'none'}),html.Div(route(),id='page-route',style={'display':'none'}),html.Div(methods(),id='page-methods',style={'display':'none'}),html.Div(historical_evidence(),id='page-evidence',style={'display':'none'}),html.Div(household_research(),id='page-households',style={'display':'none'}),html.Div(household_evidence(),id='page-hh-evidence',style={'display':'none'}),html.Div(systems_research(),id='page-systems',style={'display':'none'}),html.Div(flexibility_research(),id='page-flexibility',style={'display':'none'}),html.Div(choice_research(),id='page-choices',style={'display':'none'})]),html.P('Research prototype · November 2026 · All figures nominal USD unless labeled otherwise.',className='small')],className='wrap')
@app.callback(*[Output(f'page-{name}', 'style') for name in ('housing','history','valuation','route','methods','evidence','households','hh-evidence','systems','flexibility','choices')],Input('tabs','value'))
def page(tab):
    return tuple({} if name == tab else {'display':'none'} for name in ('housing','history','valuation','route','methods','evidence','households','hh-evidence','systems','flexibility','choices'))
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
@app.callback(Output('systems-chart','figure'),Output('systems-note','children'),Input('tabs','value'))
def systems_chart(_): return indexed_chart()

@app.callback(Output('systems-result','children'),Input('sys-income','value'),Input('sys-essential','value'),Input('sys-gain','value'),Input('sys-target','value'))
def systems_calc(income,essential,gain,target):
    r=income_gain_value(income,essential/100,gain,target)
    return html.Div([html.P(f"Annual residual before gain: ${r['before']:,.0f}; after gain: ${r['after']:,.0f}."),html.P(f"Years to accumulate target: {r['years_before']:.1f} → {r['years_after']:.1f} (starting at zero; no return).")],className='note')

@app.callback(Output('flex-result','children'),Input('flex-essential','value'),Input('flex-runway','value'),Input('flex-move','value'),Input('flex-income','value'))
def flex_calc(essential,runway,move,income):
    v=flexibility_cost(essential,runway,move,income)
    return html.Div([html.H3(f"Reference liquidity requirement: ${v['required']:,.0f}"),html.P(f"Equivalent to {v['income_share']:.1%} of annual net income; {v['months_income']:.1f} months of take-home pay.")],className='note')

@app.callback(Output('choice-results','children'),Output('choice-chart','figure'),Input('choice-job','value'),Input('choice-business','value'),Input('choice-operating','value'),Input('choice-resale','value'),Input('choice-start','value'))
def choice_calc(job,business,operating,resale,start):
    v=five_year_outcome(job,business,operating,start,resale)
    fig=go.Figure(go.Bar(x=['Cash before sale','Net sale proceeds','Liquid funds after sale'],y=[v['cash_before_sale'],v['net_sale_proceeds'],v['liquid_after_sale']],marker_color=['#9aa9a3','#e5bd79','#9ed4bc']))
    fig.update_layout(yaxis_title='Nominal USD; no return assumed')
    summary=html.Div([html.P(f"Monthly loan payment: ${v['payment']:,.0f}; net monthly savings: ${v['monthly_saving']:,.0f}."),html.P(f"Outstanding loan at 60 months: ${v['loan_balance']:,.0f}; net sale proceeds: ${v['net_sale_proceeds']:,.0f}."),html.H3(f"Liquid funds after hypothetical sale: ${v['liquid_after_sale']:,.0f}"),html.P('Business income is net of business expenses. Negative monthly savings represent cash shortfalls, not an automatically financeable outcome.',className='small')])
    return summary,figure_style(fig)

@app.callback(Output('choice-opportunity','children'),Input('choice-benefit','value'),Input('choice-fixedcost','value'),Input('choice-mobilecost','value'))
def choice_opportunity(benefit,fixed,mobile):
    a=opportunity_value(benefit,fixed);b=opportunity_value(benefit,mobile)
    return html.P(f'Stationary net exercise value: ${a:,.0f}; mobile net exercise value: ${b:,.0f}; modeled difference: ${b-a:+,.0f}.',className='note')

if __name__=='__main__':app.run(debug=True)
