"""Transparent household economies and financial-readiness scenario calculations.

These are scenario equations, not historical estimates. Do not label outputs as observed.
"""
from math import sqrt


def household_budget(adults: int, earners: int, fixed_monthly: float, variable_per_person: float,
                     net_income_per_earner: float, dependents: int = 0,
                     dependent_variable: float = 0) -> dict:
    if not isinstance(adults, int) or adults < 1:
        raise ValueError('adults must be a positive integer')
    if not isinstance(earners, int) or not 0 <= earners <= adults:
        raise ValueError('earners must be between zero and adults')
    if not isinstance(dependents, int) or dependents < 0:
        raise ValueError('dependents must be nonnegative')
    if min(fixed_monthly, variable_per_person, net_income_per_earner, dependent_variable) < 0:
        raise ValueError('expenses and earnings must be nonnegative')
    people = adults + dependents
    expenses = fixed_monthly + adults * variable_per_person + dependents * dependent_variable
    income = earners * net_income_per_earner
    surplus = income - expenses
    return {'adults': adults, 'earners': earners, 'dependents': dependents,
            'total_people': people, 'expenses': expenses, 'per_person_cost': expenses / people,
            'per_adult_cost': expenses / adults, 'income': income, 'surplus': surplus,
            'savings_rate': surplus / income if income > 0 else None,
            'equivalized_income': income / sqrt(people)}


def readiness_budget(monthly_income: float, monthly_essentials: float, liquid_savings: float,
                     reserve_months: float = 3, transition_cost: float = 0,
                     minimum_savings_rate: float = 0.1) -> dict:
    if min(monthly_income, monthly_essentials, liquid_savings, reserve_months, transition_cost) < 0:
        raise ValueError('inputs must be nonnegative')
    if not 0 <= minimum_savings_rate <= 1:
        raise ValueError('minimum_savings_rate must be within [0,1]')
    surplus = monthly_income - monthly_essentials
    required = reserve_months * monthly_essentials + transition_cost
    return {'monthly_surplus': surplus, 'reserve_target': required,
            'reserve_coverage_months': (liquid_savings / monthly_essentials if monthly_essentials else None),
            'savings_rate': surplus / monthly_income if monthly_income else None,
            'cashflow_positive': surplus >= 0,
            'reserve_ready': liquid_savings >= required,
            'savings_ready': monthly_income > 0 and surplus / monthly_income >= minimum_savings_rate,
            'fully_ready': surplus >= 0 and liquid_savings >= required and monthly_income > 0 and surplus / monthly_income >= minimum_savings_rate,
            'months_to_reserve': (max(0, required - liquid_savings) / surplus if surplus > 0 else (0.0 if liquid_savings >= required else None))}


def readiness_by_age(frame, threshold_months=3, min_savings_rate=0.1):
    """Calculate age-specific observed readiness from validated *user-supplied* microdata.

    Required columns: year, age, household_id, monthly_income, monthly_essentials,
    liquid_savings, adults, dependents. Rows are one household-year; age is the
    reference adult's age. No weighting is implied: outputs are unweighted.
    """
    import pandas as pd
    required = {'year','age','household_id','monthly_income','monthly_essentials',
                'liquid_savings','adults','dependents'}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f'Missing required columns: {sorted(missing)}')
    if frame.empty:
        raise ValueError('Input microdata are empty')
    if frame.duplicated(['year','household_id']).any():
        raise ValueError('Duplicate household-year records')
    d = frame.copy()
    for col in ['year','age','monthly_income','monthly_essentials','liquid_savings','adults','dependents']:
        d[col] = pd.to_numeric(d[col],errors='raise')
    if d[list(required - {'household_id'})].isna().any().any():
        raise ValueError('Missing numeric values')
    if (d[['monthly_income','monthly_essentials','liquid_savings','adults','dependents']] < 0).any().any() or (d.adults < 1).any():
        raise ValueError('Invalid household values')
    if not d.age.between(18,100).all():
        raise ValueError('Age must be between 18 and 100')
    d['ready'] = ((d.monthly_income > 0) &
                  ((d.monthly_income - d.monthly_essentials) / d.monthly_income.replace(0,float('nan')) >= min_savings_rate) &
                  (d.liquid_savings >= threshold_months * d.monthly_essentials))
    result = d.groupby(['year','age'],as_index=False).agg(households=('ready','size'),ready_count=('ready','sum'),readiness_share=('ready','mean'))
    return result.sort_values(['year','age']).reset_index(drop=True)
