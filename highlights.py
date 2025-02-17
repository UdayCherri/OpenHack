import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.patches import Rectangle

# plt.style.use('seaborn')

COLORS = {
    'high': '#FF6B6B',
    'low': '#4ECDC4',
    'range_fill': '#A8E6CF',
    'range_line': '#3D84A8',
    'text': '#2C3E50',
    'grid': '#DAE1E7'
}

def create_blood_test_plots(parsed_report, output_folder="abnormal_param_plots"):
  try:
    os.makedirs(output_folder, exist_ok=True)

    blood_results = parsed_report.lab_results
    abnormal_params = {k: v for k, v in blood_results.items() if v['status'] != 'Normal'}

    for param, details in abnormal_params.items():
        value = float(details['value'])
        unit = details['unit']
        ref_range = details['reference_range']
        lower, upper = map(float, ref_range.split('-'))

        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        ax.set_facecolor('#F8FBFF')

        rect = Rectangle((0.7, lower), 0.6, upper-lower,
                        facecolor=COLORS['range_fill'],
                        alpha=0.3,
                        label='Reference Range')
        ax.add_patch(rect)

        is_high = value > upper
        point_color = COLORS['high'] if is_high else COLORS['low']

        for alpha in [0.1, 0.2, 0.3]:
            ax.scatter(1, value,
                      s=300 + (1-alpha)*200,
                      color=point_color,
                      alpha=alpha,
                      zorder=4)

        scatter = ax.scatter(1, value,
                           s=200,
                           color=point_color,
                           marker='o',
                           edgecolor='white',
                           linewidth=2,
                           zorder=5,
                           label=f"Result: {value} {unit}")

        if is_high:
            ax.vlines(x=1, ymin=upper, ymax=value,
                     colors=point_color,
                     linestyles='--',
                     alpha=0.6,
                     linewidth=2)
        elif value < lower:
            ax.vlines(x=1, ymin=value, ymax=lower,
                     colors=point_color,
                     linestyles='--',
                     alpha=0.6,
                     linewidth=2)

        ax.set_xlim(0.5, 1.5)
        ax.set_ylim(min(lower * 0.9, value * 0.9),
                    max(upper * 1.1, value * 1.1))

        ax.set_xticks([])

        for y in [lower, upper]:
            ax.axhline(y=y,
                      color=COLORS['range_line'],
                      linestyle='--',
                      alpha=0.4,
                      linewidth=2)

        for y, label in [(lower, 'Lower'), (upper, 'Upper')]:
            ax.text(0.6, y, f'{label}: {y}',
                    verticalalignment='bottom',
                    horizontalalignment='right',
                    fontsize=10,
                    color='white',
                    bbox=dict(facecolor=COLORS['range_line'],
                            alpha=0.7,
                            pad=3,
                            boxstyle='round,pad=0.5'))

        ax.grid(True, axis='y', linestyle=':', alpha=0.2, color=COLORS['grid'])

        plt.title(f"{param} Test Result",
                 pad=20,
                 fontsize=16,
                 fontweight='bold',
                 color=COLORS['text'])
        plt.ylabel(f"Value ({unit})",
                  fontsize=12,
                  color=COLORS['text'])

        status_color = COLORS['high'] if is_high else COLORS['low']
        status_text = 'HIGH' if is_high else 'LOW'

        bbox_props = dict(boxstyle="round,pad=0.5",
                         fc=status_color,
                         ec="white",
                         alpha=0.8)
        plt.text(0.98, 0.02, status_text,
                transform=ax.transAxes,
                color='white',
                fontsize=12,
                fontweight='bold',
                bbox=bbox_props,
                horizontalalignment='right',
                verticalalignment='bottom')

        legend = plt.legend(loc="upper right",
                          fontsize=10,
                          framealpha=0.95,
                          shadow=True)
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_edgecolor(COLORS['range_line'])

        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS['range_line'])
            spine.set_linewidth(1.5)

        plt.tight_layout()

        save_path = os.path.join(output_folder, f"{param.replace(' ', '_')}.png")
        plt.savefig(save_path,
                   bbox_inches="tight",
                   dpi=300,
                   facecolor='white',
                   edgecolor='none')
        plt.close()

    print(f"Plots saved in: {output_folder} with vibrant color scheme")
  except Exception as e:
    print(e)