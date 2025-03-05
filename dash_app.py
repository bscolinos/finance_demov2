import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL, no_update
import os
import json
import singlestoredb as s2
from dotenv import load_dotenv
import dash_bootstrap_components as dbc

load_dotenv()

# Import your components and services
from components import portfolio, news, charts
from services.stock_service import StockService
from services.news_service import NewsService
from services.ai_service import AIService
from services.custom_investment_agent2 import get_additional_pages

def insert_optimized_portfolio(optimized_portfolio_data: dict, user_id: str):
    """
    Inserts optimized portfolio positions into SingleStore.
    """
    config = {
        "host": os.getenv('host'),
        "port": os.getenv('port'),
        "user": os.getenv('user'),
        "password": os.getenv('password'),
        "database": os.getenv('database')
    }
    connection = s2.connect(**config)
    cursor = connection.cursor()

    # Create table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS optimized_portfolio (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(100),
        symbol VARCHAR(10),
        quantity INT,
        target_allocation FLOAT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Clear previous optimizations for this user
    cursor.execute("DELETE FROM optimized_portfolio WHERE user_id = %s", (user_id, ))

    insert_query = '''
    INSERT INTO optimized_portfolio (user_id, symbol, quantity, target_allocation)
    VALUES (%s, %s, %s, %s);
    '''
    for holding in optimized_portfolio_data.get("optimized_holdings", []):
        data_tuple = (
            user_id,
            holding["symbol"],
            holding["quantity"],
            holding["target_allocation"]
        )
        cursor.execute(insert_query, data_tuple)

    connection.commit()
    cursor.close()
    connection.close()

# Define the base pages
base_pages = ["Welcome", "Portfolio Dashboard", "News Tracker", "AI Insights"]

# Initialize the Dash app with Bootstrap components and Font Awesome
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css"
    ],
    suppress_callback_exceptions=True
)
server = app.server  # For deployment purposes

# Define custom styles
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "250px",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "boxShadow": "1px 0 5px rgba(0,0,0,0.1)"
}

CONTENT_STYLE = {
    "marginLeft": "250px",
    "padding": "2rem 3rem",
    "backgroundColor": "#fff"
}

CARD_STYLE = {
    "boxShadow": "0 4px 8px 0 rgba(0,0,0,0.1)",
    "borderRadius": "8px",
    "padding": "20px",
    "marginBottom": "20px",
    "backgroundColor": "white"
}

# Updated navbar with a clickable brand
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.I(className="fas fa-chart-line me-2", style={"fontSize": "24px"})),
                        dbc.Col(dbc.NavbarBrand("AI Financial Advisor", className="ms-2", id="navbar-brand")),
                    ],
                    align="center",
                ),
                href="#",
                style={"textDecoration": "none"},
            )
        ]
    ),
    color="primary",
    dark=True,
    className="mb-4",
)

# Define the welcome_page function before app.layout
def welcome_page(user_data):
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Welcome to AI Financial Advisor", className="text-primary mb-4"),
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Get Started", className="card-title mb-4"),
                        dbc.Form([
                            dbc.Row([
                                dbc.Label("Enter your name:", width=12, className="mb-2"),
                                dbc.Col([
                                    dbc.Input(
                                        id='user-name',
                                        type='text',
                                        placeholder='Your name',
                                        value=user_data.get('user_id', ''),
                                        className="mb-3"
                                    )
                                ])
                            ]),
                            dbc.Row([
                                dbc.Label("Enter your investment goals:", width=12, className="mb-2"),
                                dbc.Col([
                                    dbc.Textarea(
                                        id='investment-goals',
                                        placeholder='e.g., I want to save for retirement, college funds for kids, etc.',
                                        value=user_data.get('investment_goals', ''),
                                        className="mb-3",
                                        style={"height": "120px"}
                                    )
                                ])
                            ]),
                            dbc.Button(
                                "Create My Financial Plan", 
                                id='submit-btn', 
                                color="primary", 
                                className="mt-3"
                            ),
                        ])
                    ])
                ], className="mb-4"),
                dbc.Card([
                    dbc.CardBody([
                        html.Div(id='welcome-output')
                    ])
                ])
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Why Choose AI Financial Advisor?", className="card-title"),
                        html.P("Our AI-powered platform offers personalized financial advice tailored to your goals."),
                        html.Ul([
                            html.Li("Personalized investment strategies"),
                            html.Li("Real-time market analysis"),
                            html.Li("AI-driven portfolio optimization"),
                            html.Li("Customized goal planning"),
                        ])
                    ])
                ], className="mb-4"),
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Market Insights", className="card-title"),
                        html.P("Today's Market Overview"),
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Div("S&P 500", className="fw-bold"),
                                html.Div([
                                    html.Span("4,587.64 ", className="text-success"),
                                    html.Span("+0.57%", className="text-success")
                                ], className="d-flex justify-content-between")
                            ]),
                            dbc.ListGroupItem([
                                html.Div("NASDAQ", className="fw-bold"),
                                html.Div([
                                    html.Span("14,346.02 ", className="text-success"),
                                    html.Span("+0.75%", className="text-success")
                                ], className="d-flex justify-content-between")
                            ]),
                            dbc.ListGroupItem([
                                html.Div("10-YR Treasury", className="fw-bold"),
                                html.Div([
                                    html.Span("1.67% ", className="text-danger"),
                                    html.Span("-0.02%", className="text-danger")
                                ], className="d-flex justify-content-between")
                            ])
                        ])
                    ])
                ])
            ], width=4)
        ])
    ])

app.layout = html.Div([
    # Stores to hold user data and the list of available pages
    dcc.Store(id='store-pages', data=base_pages),
    dcc.Store(id='store-user', data={'user_id': '', 'investment_goals': '', 'custom_portfolio': {}}),
    dcc.Store(id='active-page', data='Welcome'),  # Store for active page
    
    # Sidebar navigation
    html.Div([
        html.H4("Navigation", className="text-primary"),
        html.Hr(),
        html.Div(id='page-selector-nav'),  # Will be filled by callback
    ], style=SIDEBAR_STYLE),
    
    # Main content area
    html.Div([
        # Navbar
        dbc.Navbar(
            dbc.Container(
                [
                    html.A(
                        dbc.Row(
                            [
                                dbc.Col(html.I(className="fas fa-chart-line me-2", style={"fontSize": "24px"})),
                                html.Span("AI Financial Advisor", className="ms-2 navbar-brand")
                            ],
                            align="center",
                        ),
                        id="navbar-home-link",
                        href="#",
                        style={"textDecoration": "none", "color": "white"},
                    )
                ]
            ),
            color="primary",
            dark=True,
            className="mb-4",
        ),
        # Main content
        html.Div(id='main-content')
    ], style=CONTENT_STYLE)
])

# Navigation builder callback using built-in color and outline props
@app.callback(
    Output('page-selector-nav', 'children'),
    [Input('store-pages', 'data'),
     Input('active-page', 'data')]
)
def build_navigation(pages, active_page):
    nav_items = []
    icons = {
        "Welcome": "fas fa-home",
        "Portfolio Dashboard": "fas fa-chart-pie",
        "News Tracker": "fas fa-newspaper",
        "AI Insights": "fas fa-robot",
        "College Savings Account": "fas fa-graduation-cap",
        "529 Plan": "fas fa-university",
        "Crypto Investments": "fab fa-bitcoin",
        "Mortgage Planning": "fas fa-home",
        "Estate Planning": "fas fa-scroll",
        "Life Insurance": "fas fa-heartbeat"
    }
    
    for page in pages:
        icon = icons.get(page, "fas fa-circle")
        is_active = page == active_page
        
        nav_items.append(
            dbc.Button(
                [
                    html.I(className=f"{icon} me-2"),
                    html.Span(page)
                ],
                id={"type": "page-nav", "index": page},
                color="primary",
                outline=not is_active,  # Solid if active, outlined otherwise
                className="mb-2 text-start w-100",
                style={"textAlign": "left", "justifyContent": "flex-start"}
            )
        )
    
    return html.Div(nav_items)

# Callback to update active page when navigation is clicked
@app.callback(
    Output('active-page', 'data'),
    [Input({"type": "page-nav", "index": ALL}, "n_clicks"),
     Input("navbar-home-link", "n_clicks")],
    [State('active-page', 'data'),
     State('store-pages', 'data')],
    allow_duplicate=True
)
def update_active_page(nav_clicks, home_clicks, current_page, pages):
    ctx = callback_context
    if not ctx.triggered:
        return current_page
        
    trigger = ctx.triggered[0]['prop_id']
    
    # Home link clicked - go to Welcome page
    if trigger == "navbar-home-link.n_clicks":
        return "Welcome"
        
    # A navigation button was clicked
    if "{" in trigger:  # Pattern-matching callback format
        button_id = json.loads(trigger.split('.')[0])
        return button_id['index']
        
    return current_page

# Callback to update main content based on active page
@app.callback(
    Output('main-content', 'children'),
    Input('active-page', 'data'),
    State('store-user', 'data')
)
def update_content(page, user_data):
    if page is None:
        page = "Welcome"  # Default to welcome page if None
    if page == "Welcome":
        return welcome_page(user_data)
    else:
        return render_page(page, user_data)

# Updated welcome page callback with debugging, error handling, and active-page update.
# We add allow_duplicate=True so that this callback can also update 'active-page' alongside the other callback.
@app.callback(
    [Output('store-user', 'data'),
     Output('store-pages', 'data'),
     Output('welcome-output', 'children'),
     Output('active-page', 'data')],
    Input('submit-btn', 'n_clicks'),
    [State('user-name', 'value'),
     State('investment-goals', 'value'),
     State('store-user', 'data'),
     State('store-pages', 'data')],
    allow_duplicate=True,
    prevent_initial_call=True
)
def update_welcome(n_clicks, user_name, investment_goals, user_data, pages):
    print("Create My Financial Plan Button clicked", n_clicks)  # Debug statement
    if n_clicks is None or n_clicks == 0:
        # Instead of preventing update, return current values
        return user_data, pages, no_update, no_update

    # Update user data with name and investment goals
    user_data['user_id'] = user_name
    user_data['investment_goals'] = investment_goals

    # Modify pages if investment goals are provided
    if investment_goals and pages == base_pages:
        pages = get_additional_pages(investment_goals, base_pages)
    else:
        pages = base_pages

    output_message = None
    new_active_page = 'Welcome'
    if investment_goals:
        try:
            ai_service = AIService()
            # Generate optimized portfolio (using an empty dict as a placeholder)
            optimized_portfolio = ai_service.optimize_portfolio({}, investment_goals)
            # Insert the optimized portfolio into the database
            insert_optimized_portfolio(optimized_portfolio, user_name)
            user_data['custom_portfolio'] = optimized_portfolio

            # Create a visual representation of the portfolio
            holdings_rows = []
            for holding in optimized_portfolio.get("optimized_holdings", []):
                holdings_rows.append(
                    dbc.ListGroupItem([
                        html.Div([
                            html.Span(holding["symbol"], className="fw-bold"),
                            html.Span(f"{holding['target_allocation']*100:.1f}%", className="badge bg-primary ms-2"),
                        ]),
                        html.Div(f"Quantity: {holding['quantity']}")
                    ])
                )

            output_message = html.Div([
                html.H5("Your Personalized Investment Plan", className="text-success mb-3"),
                html.P("Based on your goals, we've created an optimized portfolio that aligns with your objectives:"),
                dbc.ListGroup(holdings_rows, className="mb-3"),
                html.P("Your portfolio has been saved and is ready for detailed analysis!", className="text-muted")
            ])
            # Update active page to Portfolio Dashboard after plan creation
            new_active_page = "Portfolio Dashboard"
        except Exception as e:
            print("Error in processing financial plan:", e)
            output_message = html.Div("An error occurred while creating your financial plan.")
            new_active_page = "Welcome"

    return user_data, pages, output_message, new_active_page

# Callback to render pages with modernized layouts
def render_page(page, user_data):
    if page == "Welcome":
        return welcome_page(user_data)
    elif page == "Portfolio Dashboard":
        return dbc.Container([
            html.H2("Portfolio Overview", className="text-primary mb-4"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Portfolio Summary")),
                        dbc.CardBody(portfolio.display_portfolio_summary())
                    ], className="mb-4")
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Performance Charts")),
                        dbc.CardBody(charts.plot_portfolio_performance())
                    ], className="mb-4")
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Quick Actions")),
                        dbc.CardBody(portfolio.display_quick_actions())
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Market Summary")),
                        dbc.CardBody(portfolio.display_market_summary())
                    ])
                ], width=6)
            ])
        ])
    elif page == "News Tracker":
        return dbc.Container([
            html.H2("Financial News Tracker", className="text-primary mb-4"),
            dbc.Card([
                dbc.CardBody(news.display_news_dashboard())
            ])
        ])
    elif page == "AI Insights":
        portfolio_data = user_data.get('custom_portfolio', {})
        ai_service = AIService()
        portfolio_analysis = ai_service.get_portfolio_insights(portfolio_data)
        news_service = NewsService()
        market_news = news_service.get_market_news(limit=5)
        sentiment = ai_service.get_market_sentiment(market_news)
        
        return dbc.Container([
            html.H2("AI-Powered Insights", className="text-primary mb-4"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Portfolio Analysis")),
                        dbc.CardBody(portfolio_analysis)
                    ], className="mb-4")
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Market Sentiment Analysis")),
                        dbc.CardBody(sentiment)
                    ])
                ], width=12)
            ])
        ])
    elif page == "College Savings Account":
        return dbc.Container([
            html.H2("College Savings Account", className="text-primary mb-4"),
            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "This page is designed to help you with planning and managing a college savings account. "
                        "Here you can find advice on setting savings goals, recommended account types, and strategies to optimize your contributions."
                    )
                ])
            ])
        ])
    elif page == "529 Plan":
        return dbc.Container([
            html.H2("529 Plan", className="text-primary mb-4"),
            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "This page provides information on 529 plans—a tax-advantaged savings plan to encourage saving for future education costs. "
                        "You'll find details on tax benefits, investment options, and best practices for planning your child's education."
                    )
                ])
            ])
        ])
    elif page == "Crypto Investments":
        return dbc.Container([
            html.H2("Crypto Investments", className="text-primary mb-4"),
            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "This page offers insights into cryptocurrency investments. "
                        "Explore market trends, top digital assets, and strategies for diversifying your portfolio with crypto. "
                        "Leverage the latest AI insights to help you make informed decisions in the dynamic crypto market."
                    )
                ])
            ])
        ])
    elif page == "Mortgage Planning":
        return dbc.Container([
            html.H2("Mortgage Planning", className="text-primary mb-4"),
            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "This page provides information on mortgage planning. "
                        "Here you can find advice on setting savings goals, recommended account types, and strategies to optimize your contributions."
                    )
                ])
            ])
        ])
    elif page == "Estate Planning":
        return dbc.Container([
            html.H2("Estate Planning", className="text-primary mb-4"),
            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "This page provides information on estate planning. "
                        "Here you can find advice on setting savings goals, recommended account types, and strategies to optimize your contributions."
                    )
                ])
            ])
        ])
    elif page == "Life Insurance":
        return dbc.Container([
            html.H2("Life Insurance", className="text-primary mb-4"),
            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "This page provides information on life insurance. "
                        "Here you can find advice on setting savings goals, recommended account types, and strategies to optimize your contributions."
                    )
                ])
            ])
        ])
    else:
        return dbc.Container([
            html.H2("Page Not Found", className="text-danger"),
            dbc.Card([
                dbc.CardBody([
                    html.P("The requested page could not be found. Please select another option from the navigation menu.")
                ])
            ])
        ])

if __name__ == '__main__':
    app.run_server(debug=True)