"""Data visualization components."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta

def create_health_metrics_chart(metrics: List[Dict], metric_type: str) -> go.Figure:
    """Create line chart for health metrics over time."""
    if not metrics:
        return None
    
    df = pd.DataFrame(metrics)
    df['measured_at'] = pd.to_datetime(df['measured_at'])
    df = df.sort_values('measured_at')
    
    fig = go.Figure()
    
    if metric_type == "blood_pressure":
        fig.add_trace(go.Scatter(
            x=df['measured_at'],
            y=df['value'],
            name='Systolic',
            line=dict(color='#e74c3c', width=2),
            mode='lines+markers'
        ))
        if 'secondary_value' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['measured_at'],
                y=df['secondary_value'],
                name='Diastolic',
                line=dict(color='#3498db', width=2),
                mode='lines+markers'
            ))
        # Add normal range
        fig.add_hrect(y0=70, y1=120, fillcolor="green", opacity=0.1, 
                     annotation_text="Normal Range")
    
    elif metric_type == "blood_sugar":
        fig.add_trace(go.Scatter(
            x=df['measured_at'],
            y=df['value'],
            name='Blood Sugar',
            line=dict(color='#9b59b6', width=2),
            mode='lines+markers',
            fill='tozeroy',
            fillcolor='rgba(155, 89, 182, 0.1)'
        ))
        # Add normal range lines
        fig.add_hline(y=100, line_dash="dash", line_color="green", 
                     annotation_text="Normal Fasting")
        fig.add_hline(y=140, line_dash="dash", line_color="orange",
                     annotation_text="Pre-diabetic")
    
    elif metric_type == "weight":
        fig.add_trace(go.Scatter(
            x=df['measured_at'],
            y=df['value'],
            name='Weight',
            line=dict(color='#2ecc71', width=2),
            mode='lines+markers'
        ))
    
    elif metric_type == "heart_rate":
        fig.add_trace(go.Scatter(
            x=df['measured_at'],
            y=df['value'],
            name='Heart Rate',
            line=dict(color='#e74c3c', width=2),
            mode='lines+markers'
        ))
        fig.add_hrect(y0=60, y1=100, fillcolor="green", opacity=0.1)
    
    fig.update_layout(
        title=f'{metric_type.replace("_", " ").title()} Over Time',
        xaxis_title='Date',
        yaxis_title=df['unit'].iloc[0] if 'unit' in df.columns else 'Value',
        hovermode='x unified',
        template='plotly_white',
        height=350
    )
    
    return fig

def create_adherence_chart(adherence_data: List[Dict]) -> go.Figure:
    """Create medicine adherence chart."""
    if not adherence_data:
        return None
    
    df = pd.DataFrame(adherence_data)
    
    fig = go.Figure(data=[
        go.Bar(
            x=df['medicine_name'],
            y=df['adherence_percentage'],
            marker_color=['#2ecc71' if x >= 80 else '#e74c3c' for x in df['adherence_percentage']],
            text=[f'{x:.0f}%' for x in df['adherence_percentage']],
            textposition='outside'
        )
    ])
    
    fig.add_hline(y=80, line_dash="dash", line_color="orange",
                 annotation_text="Target: 80%")
    
    fig.update_layout(
        title='Medicine Adherence by Medication',
        xaxis_title='Medicine',
        yaxis_title='Adherence %',
        yaxis_range=[0, 105],
        template='plotly_white',
        height=300
    )
    
    return fig

def create_consultation_timeline(consultations: List[Dict]) -> go.Figure:
    """Create consultation timeline visualization."""
    if not consultations:
        return None
    
    df = pd.DataFrame(consultations)
    df['date'] = pd.to_datetime(df['consultation_date'])
    
    # Group by month
    df['month'] = df['date'].dt.to_period('M').astype(str)
    monthly_counts = df.groupby('month').size().reset_index(name='count')
    
    fig = go.Figure(data=[
        go.Bar(
            x=monthly_counts['month'],
            y=monthly_counts['count'],
            marker_color='#3498db',
            text=monthly_counts['count'],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='Consultations Over Time',
        xaxis_title='Month',
        yaxis_title='Number of Consultations',
        template='plotly_white',
        height=300
    )
    
    return fig

def create_health_score_gauge(score: float, max_score: float = 100) -> go.Figure:
    """Create gauge chart for health score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, max_score]},
            'bar': {'color': "#3498db"},
            'steps': [
                {'range': [0, 30], 'color': "#ffebee"},
                {'range': [30, 60], 'color': "#fff3e0"},
                {'range': [60, 80], 'color': "#e8f5e9"},
                {'range': [80, 100], 'color': "#c8e6c9"}
            ],
            'threshold': {
                'line': {'color': "green", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        },
        title={'text': "Health Score"}
    ))
    
    fig.update_layout(height=250)
    return fig

def create_appointment_calendar(appointments: List[Dict]) -> go.Figure:
    """Create appointment distribution chart."""
    if not appointments:
        return None
    
    df = pd.DataFrame(appointments)
    df['date'] = pd.to_datetime(df['appointment_date'])
    df['day'] = df['date'].dt.day_name()
    
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = df['day'].value_counts().reindex(day_order, fill_value=0)
    
    fig = go.Figure(data=[
        go.Bar(
            x=day_counts.index,
            y=day_counts.values,
            marker_color='#9b59b6'
        )
    ])
    
    fig.update_layout(
        title='Appointments by Day of Week',
        xaxis_title='Day',
        yaxis_title='Count',
        template='plotly_white',
        height=300
    )
    
    return fig
