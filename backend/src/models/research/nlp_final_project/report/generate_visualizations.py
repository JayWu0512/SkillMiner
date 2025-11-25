"""
Generate visualization plots for the Memory-Augmented LSTM research report.

This script creates:
1. Model comparison plots (X: Model, Y: Accuracy/Metrics)
2. Training progress plots (X: Epoch, Y: Metrics over time)
"""

import matplotlib.pyplot as plt
import numpy as np
import re
from pathlib import Path

# Set style for publication-quality figures
try:
    plt.style.use('seaborn-v0_8-paper')
except:
    try:
        plt.style.use('seaborn-paper')
    except:
        plt.style.use('default')
        
plt.rcParams['figure.figsize'] = (8, 5)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

# Data extracted from report_output.txt
SYNTHETIC_DATA = {
    'Model 0': {
        'epochs': list(range(1, 11)),
        'loss': [1.9220, 0.6491, 0.2400, 0.1319, 0.0974, 0.0789, 0.0687, 0.0621, 0.0578, 0.0541],
        'stm_acc': [0.000, 0.025, 0.100, 0.325, 0.275, 0.375, 0.300, 0.300, 0.325, 0.475],
        'ltm_acc': [0.000, 0.050, 0.550, 0.500, 0.600, 0.600, 0.550, 0.600, 0.700, 0.650],
        'stm_llm': [0.000, 0.123, 0.353, 0.485, 0.470, 0.520, 0.485, 0.490, 0.493, 0.570],
        'ltm_llm': [0.000, 0.090, 0.415, 0.460, 0.490, 0.465, 0.445, 0.480, 0.480, 0.495]
    },
    'Model 1': {
        'epochs': list(range(1, 11)),
        'loss': [1.9097, 0.6097, 0.2160, 0.1216, 0.0916, 0.0777, 0.0694, 0.0639, 0.0609, 0.0571],
        'stm_acc': [0.000, 0.025, 0.225, 0.350, 0.325, 0.350, 0.300, 0.275, 0.425, 0.400],
        'ltm_acc': [0.000, 0.100, 0.450, 0.700, 0.550, 0.600, 0.650, 0.650, 0.700, 0.650],
        'stm_llm': [0.000, 0.172, 0.382, 0.470, 0.468, 0.490, 0.483, 0.480, 0.525, 0.505],
        'ltm_llm': [0.000, 0.180, 0.385, 0.490, 0.445, 0.480, 0.500, 0.495, 0.515, 0.510]
    },
    'Model 2': {
        'epochs': list(range(1, 11)),
        'loss': [1.8975, 0.6290, 0.2290, 0.1266, 0.0939, 0.0788, 0.0692, 0.0632, 0.0571, 0.0522],
        'stm_acc': [0.000, 0.000, 0.150, 0.300, 0.375, 0.350, 0.400, 0.425, 0.375, 0.350],
        'ltm_acc': [0.000, 0.150, 0.300, 0.550, 0.550, 0.650, 0.650, 0.650, 0.750, 0.650],
        'stm_llm': [0.000, 0.158, 0.330, 0.480, 0.482, 0.480, 0.527, 0.518, 0.517, 0.505],
        'ltm_llm': [0.000, 0.145, 0.350, 0.475, 0.500, 0.500, 0.495, 0.475, 0.555, 0.515]
    },
    'Model 3': {
        'epochs': list(range(1, 11)),
        'loss': [1.9378, 0.6317, 0.2249, 0.1254, 0.0930, 0.0781, 0.0699, 0.0634, 0.0588, 0.0558],
        'stm_acc': [0.000, 0.050, 0.200, 0.375, 0.375, 0.500, 0.375, 0.375, 0.350, 0.350],
        'ltm_acc': [0.000, 0.100, 0.450, 0.750, 0.800, 0.600, 0.700, 0.750, 0.650, 0.650],
        'stm_llm': [0.000, 0.160, 0.378, 0.505, 0.500, 0.532, 0.517, 0.500, 0.500, 0.522],
        'ltm_llm': [0.000, 0.105, 0.405, 0.495, 0.505, 0.475, 0.490, 0.535, 0.500, 0.510]
    },
    'Model 4': {
        'epochs': list(range(1, 11)),
        'loss': [1.8962, 0.6234, 0.2426, 0.1466, 0.1116, 0.0933, 0.0818, 0.0740, 0.0687, 0.0627],
        'stm_acc': [0.000, 0.000, 0.150, 0.350, 0.375, 0.325, 0.375, 0.425, 0.550, 0.350],
        'ltm_acc': [0.000, 0.000, 0.150, 0.750, 0.800, 0.700, 0.600, 0.600, 0.750, 0.500],
        'stm_llm': [0.000, 0.060, 0.330, 0.465, 0.512, 0.508, 0.500, 0.515, 0.512, 0.487],
        'ltm_llm': [0.000, 0.070, 0.250, 0.510, 0.535, 0.495, 0.485, 0.500, 0.505, 0.470]
    }
}

REAL_DATA = {
    'Model 0': {
        'epochs': list(range(1, 11)),
        'loss': [2.4974, 2.0891, 1.9274, 1.8149, 1.7257, 1.6507, 1.5855, 1.5244, 1.4691, 1.4217],
        'stm_difflib': [0.027, 0.035, 0.034, 0.039, 0.040, 0.044, 0.042, 0.044, 0.050, 0.060],
        'ltm_difflib': [0.025, 0.028, 0.027, 0.030, 0.028, 0.050, 0.032, 0.039, 0.051, 0.062]
    },
    'Model 1': {
        'epochs': list(range(1, 11)),
        'loss': [2.5077, 2.1059, 1.9473, 1.8331, 1.7427, 1.6668, 1.5980, 1.5370, 1.4804, 1.4286],
        'stm_difflib': [0.032, 0.029, 0.032, 0.033, 0.036, 0.045, 0.059, 0.051, 0.065, 0.063],
        'ltm_difflib': [0.022, 0.020, 0.022, 0.022, 0.027, 0.040, 0.050, 0.047, 0.051, 0.050]
    },
    'Model 2': {
        'epochs': list(range(1, 11)),
        'loss': [2.4895, 2.0783, 1.9200, 1.8080, 1.7187, 1.6437, 1.5775, 1.5164, 1.4483, 1.3974],
        'stm_difflib': [0.030, 0.033, 0.034, 0.037, 0.040, 0.045, 0.050, 0.052, 0.055, 0.061],
        'ltm_difflib': [0.024, 0.023, 0.027, 0.026, 0.028, 0.032, 0.034, 0.033, 0.043, 0.041]
    },
    'Model 3': {
        'epochs': list(range(1, 11)),
        'loss': [2.4910, 2.0844, 1.9222, 1.8090, 1.7245, 1.6492, 1.5811, 1.5209, 1.4651, 1.4145],
        'stm_difflib': [0.035, 0.033, 0.036, 0.038, 0.047, 0.049, 0.052, 0.052, 0.057, 0.059],
        'ltm_difflib': [0.022, 0.022, 0.030, 0.029, 0.031, 0.039, 0.042, 0.040, 0.042, 0.042]
    },
    'Model 4': {
        'epochs': list(range(1, 11)),
        'loss': [2.5147, 2.1149, 1.9569, 1.8441, 1.7479, 1.6693, 1.6001, 1.5384, 1.4816, 1.4289],
        'stm_difflib': [0.032, 0.031, 0.034, 0.037, 0.043, 0.046, 0.041, 0.059, 0.053, 0.071],
        'ltm_difflib': [0.019, 0.024, 0.027, 0.028, 0.030, 0.028, 0.031, 0.033, 0.041, 0.062]
    }
}

def plot_model_comparison_synthetic():
    """Plot 1: Model comparison for synthetic dataset (X: Model, Y: Accuracy)"""
    models = ['Model 0', 'Model 1', 'Model 2', 'Model 3', 'Model 4']
    model_labels = ['0 (Base)', '1 (Sum)', '2 (Sum+Tok)', '3 (Sum+Tok+NER)', '4 (Full)']
    
    # Get best epoch accuracies
    stm_accs = []
    ltm_accs = []
    
    for model in models:
        data = SYNTHETIC_DATA[model]
        # Find best epoch (highest combined accuracy or best LTM)
        best_epoch_idx = np.argmax([a + l for a, l in zip(data['stm_acc'], data['ltm_acc'])])
        stm_accs.append(data['stm_acc'][best_epoch_idx])
        ltm_accs.append(data['ltm_acc'][best_epoch_idx])
    
    fig, ax = plt.subplots(figsize=(9, 6))
    x = np.arange(len(models))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, stm_accs, width, label='STM Accuracy', alpha=0.8, color='#2E86AB')
    bars2 = ax.bar(x + width/2, ltm_accs, width, label='LTM Accuracy', alpha=0.8, color='#A23B72')
    
    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Accuracy', fontweight='bold')
    ax.set_title('Model Comparison: Synthetic Dataset (Best Epoch)', fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, rotation=0)
    ax.legend(loc='upper left', frameon=True)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim([0, 0.90])  # Increased upper limit to accommodate labels
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.015,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('model_comparison_synthetic.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('model_comparison_synthetic.png', dpi=300, bbox_inches='tight')
    print("Saved: model_comparison_synthetic.pdf and .png")
    plt.close()

def plot_model_comparison_real():
    """Plot 2: Model comparison for real dataset (X: Model, Y: Metrics)"""
    models = ['Model 0', 'Model 1', 'Model 2', 'Model 3', 'Model 4']
    model_labels = ['0 (Base)', '1 (Sum)', '2 (Sum+Tok)', '3 (Sum+Tok+NER)', '4 (Full)']
    
    # Get final epoch metrics (epoch 10)
    losses = []
    stm_difflibs = []
    ltm_difflibs = []
    
    for model in models:
        data = REAL_DATA[model]
        losses.append(data['loss'][-1])
        stm_difflibs.append(data['stm_difflib'][-1])
        ltm_difflibs.append(data['ltm_difflib'][-1])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Loss
    x = np.arange(len(models))
    ax1.plot(x, losses, marker='o', linewidth=2, markersize=8, color='#F18F01', label='Loss')
    ax1.set_xlabel('Model', fontweight='bold')
    ax1.set_ylabel('Loss', fontweight='bold')
    ax1.set_title('Model Comparison: Real Dataset Loss (Epoch 10)', fontweight='bold', pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(model_labels, rotation=0)
    ax1.grid(alpha=0.3, linestyle='--')
    ax1.legend(frameon=True)
    
    # Set y-axis limits with padding for labels
    loss_min, loss_max = min(losses), max(losses)
    loss_range = loss_max - loss_min
    ax1.set_ylim([loss_min - 0.05, loss_max + 0.05])
    
    # Add value labels
    for i, (xi, yi) in enumerate(zip(x, losses)):
        ax1.text(xi, yi + 0.01, f'{yi:.3f}', ha='center', va='bottom', fontsize=9)
    
    # Plot 2: Difflib scores
    width = 0.35
    ax2.bar(x - width/2, stm_difflibs, width, label='STM Difflib', alpha=0.8, color='#C73E1D')
    ax2.bar(x + width/2, ltm_difflibs, width, label='LTM Difflib', alpha=0.8, color='#6A994E')
    ax2.set_xlabel('Model', fontweight='bold')
    ax2.set_ylabel('Difflib Score', fontweight='bold')
    ax2.set_title('Model Comparison: Real Dataset Difflib Scores (Epoch 10)', fontweight='bold', pad=15)
    ax2.set_xticks(x)
    ax2.set_xticklabels(model_labels, rotation=0)
    ax2.legend(frameon=True)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Set y-axis limits with padding for labels
    difflib_max = max(max(stm_difflibs), max(ltm_difflibs))
    ax2.set_ylim([0, difflib_max * 1.15])
    
    # Add value labels
    for i, (stm, ltm) in enumerate(zip(stm_difflibs, ltm_difflibs)):
        ax2.text(i - width/2, stm + difflib_max * 0.01, f'{stm:.3f}', ha='center', va='bottom', fontsize=8)
        ax2.text(i + width/2, ltm + difflib_max * 0.01, f'{ltm:.3f}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig('model_comparison_real.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('model_comparison_real.png', dpi=300, bbox_inches='tight')
    print("Saved: model_comparison_real.pdf and .png")
    plt.close()

def plot_training_progress_synthetic():
    """Plot 3: Training progress for synthetic dataset (X: Epoch, Y: Metrics)"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    models = ['Model 0', 'Model 1', 'Model 2', 'Model 3', 'Model 4']
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']
    
    # Plot 1: Loss over epochs
    ax = axes[0, 0]
    for i, model in enumerate(models):
        data = SYNTHETIC_DATA[model]
        ax.plot(data['epochs'], data['loss'], marker='o', linewidth=2, markersize=5, 
               label=model, color=colors[i], alpha=0.8)
    ax.set_xlabel('Epoch', fontweight='bold')
    ax.set_ylabel('Loss', fontweight='bold')
    ax.set_title('Training Loss: Synthetic Dataset', fontweight='bold', pad=15)
    ax.legend(frameon=True, loc='upper right')
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim([0.5, 10.5])
    
    # Plot 2: STM Accuracy over epochs
    ax = axes[0, 1]
    for i, model in enumerate(models):
        data = SYNTHETIC_DATA[model]
        ax.plot(data['epochs'], data['stm_acc'], marker='o', linewidth=2, markersize=5, 
               label=model, color=colors[i], alpha=0.8)
    ax.set_xlabel('Epoch', fontweight='bold')
    ax.set_ylabel('STM Accuracy', fontweight='bold')
    ax.set_title('STM Accuracy: Synthetic Dataset', fontweight='bold', pad=15)
    ax.legend(frameon=True, loc='lower right')
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim([0.5, 10.5])
    ax.set_ylim([-0.05, 0.6])
    
    # Plot 3: LTM Accuracy over epochs
    ax = axes[1, 0]
    for i, model in enumerate(models):
        data = SYNTHETIC_DATA[model]
        ax.plot(data['epochs'], data['ltm_acc'], marker='o', linewidth=2, markersize=5, 
               label=model, color=colors[i], alpha=0.8)
    ax.set_xlabel('Epoch', fontweight='bold')
    ax.set_ylabel('LTM Accuracy', fontweight='bold')
    ax.set_title('LTM Accuracy: Synthetic Dataset', fontweight='bold', pad=15)
    ax.legend(frameon=True, loc='lower right')
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim([0.5, 10.5])
    ax.set_ylim([-0.05, 0.85])
    
    # Plot 4: Combined view (STM + LTM)
    ax = axes[1, 1]
    for i, model in enumerate(models):
        data = SYNTHETIC_DATA[model]
        ax.plot(data['epochs'], data['stm_acc'], marker='o', linewidth=2, markersize=5, 
               label=f'{model} STM', color=colors[i], alpha=0.6, linestyle='-')
        ax.plot(data['epochs'], data['ltm_acc'], marker='s', linewidth=2, markersize=5, 
               label=f'{model} LTM', color=colors[i], alpha=0.8, linestyle='--')
    ax.set_xlabel('Epoch', fontweight='bold')
    ax.set_ylabel('Accuracy', fontweight='bold')
    ax.set_title('STM vs LTM Accuracy: Synthetic Dataset', fontweight='bold', pad=15)
    ax.legend(frameon=True, loc='lower right', ncol=2, fontsize=8)
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim([0.5, 10.5])
    ax.set_ylim([-0.05, 0.85])
    
    plt.tight_layout()
    plt.savefig('training_progress_synthetic.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('training_progress_synthetic.png', dpi=300, bbox_inches='tight')
    print("Saved: training_progress_synthetic.pdf and .png")
    plt.close()

def plot_training_progress_real():
    """Plot 4: Training progress for real dataset (X: Epoch, Y: Metrics)"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    models = ['Model 0', 'Model 1', 'Model 2', 'Model 3', 'Model 4']
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']
    
    # Plot 1: Loss over epochs
    ax = axes[0]
    for i, model in enumerate(models):
        data = REAL_DATA[model]
        ax.plot(data['epochs'], data['loss'], marker='o', linewidth=2, markersize=5, 
               label=model, color=colors[i], alpha=0.8)
    ax.set_xlabel('Epoch', fontweight='bold')
    ax.set_ylabel('Loss', fontweight='bold')
    ax.set_title('Training Loss: Real Dataset (Dog-Cat)', fontweight='bold', pad=15)
    ax.legend(frameon=True, loc='upper right')
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim([0.5, 10.5])
    
    # Plot 2: Difflib scores over epochs
    ax = axes[1]
    for i, model in enumerate(models):
        data = REAL_DATA[model]
        ax.plot(data['epochs'], data['stm_difflib'], marker='o', linewidth=2, markersize=5, 
               label=f'{model} STM', color=colors[i], alpha=0.6, linestyle='-')
        ax.plot(data['epochs'], data['ltm_difflib'], marker='s', linewidth=2, markersize=5, 
               label=f'{model} LTM', color=colors[i], alpha=0.8, linestyle='--')
    ax.set_xlabel('Epoch', fontweight='bold')
    ax.set_ylabel('Difflib Score', fontweight='bold')
    ax.set_title('Difflib Scores: Real Dataset (Dog-Cat)', fontweight='bold', pad=15)
    ax.legend(frameon=True, loc='lower right', ncol=2, fontsize=8)
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim([0.5, 10.5])
    
    plt.tight_layout()
    plt.savefig('training_progress_real.pdf', dpi=300, bbox_inches='tight')
    plt.savefig('training_progress_real.png', dpi=300, bbox_inches='tight')
    print("Saved: training_progress_real.pdf and .png")
    plt.close()

def main():
    """Generate all visualization plots"""
    print("Generating visualization plots...")
    print("=" * 50)
    
    plot_model_comparison_synthetic()
    plot_model_comparison_real()
    plot_training_progress_synthetic()
    plot_training_progress_real()
    
    print("=" * 50)
    print("All visualizations generated successfully!")
    print("\nGenerated files:")
    print("  - model_comparison_synthetic.pdf/.png")
    print("  - model_comparison_real.pdf/.png")
    print("  - training_progress_synthetic.pdf/.png")
    print("  - training_progress_real.pdf/.png")

if __name__ == '__main__':
    main()

