import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

def _circle_layout(K, radius=1.0):
    angles = np.linspace(0, 2*np.pi, K, endpoint=False)
    xs = radius * np.cos(angles)
    ys = radius * np.sin(angles)
    return np.stack([xs, ys], axis=1)  # shape (K, 2)

def _jitter(n):
    # small jitter cloud so points don't overlap exactly
    return 0.04 * np.random.randn(n, 2)

def animate_paths(trace, n_clusters, title="Taxi allocation: Recommendation vs Random",
                  save_mp4="taxi_sim.mp4", save_gif="taxi_sim.gif"):
    T = trace["T"]
    pos = _circle_layout(n_clusters, radius=1.0)

    # figure with two panels
    fig, axes = plt.subplots(1, 2, figsize=(10,5), sharex=True, sharey=True)
    ax_rec, ax_rnd = axes
    for ax, name in zip(axes, ["Recommendation", "Random"]):
        ax.set_title(name)
        ax.set_aspect('equal')
        ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4)
        ax.axis('off')
        # draw cluster nodes
        ax.scatter(pos[:,0], pos[:,1], s=200, marker='o', edgecolor='k', facecolor='white')
        for k,(x,y) in enumerate(pos):
            ax.text(x, y+0.12, f"C{k}", ha='center', va='bottom', fontsize=10)

    # scatters for drivers
    scat_rec = ax_rec.scatter([], [], s=20)
    scat_rnd = ax_rnd.scatter([], [], s=20)

    # text boxes for revenues and step
    text_rec = ax_rec.text(0.02, 0.98, "", transform=ax_rec.transAxes, va='top', ha='left')
    text_rnd = ax_rnd.text(0.02, 0.98, "", transform=ax_rnd.transAxes, va='top', ha='left')
    title_text = fig.suptitle(title, y=0.98)

    # arrow artists (we'll clear and redraw each frame)
    arrows_rec = []
    arrows_rnd = []

    def update(frame):
        # clear old arrows
        for a in arrows_rec: a.remove()
        for a in arrows_rnd: a.remove()
        arrows_rec.clear(); arrows_rnd.clear()

        # pull slot data
        oc_rec = trace["rec"]["old_clusters"][frame]
        nc_rec = trace["rec"]["new_clusters"][frame]
        oc_rnd = trace["rnd"]["old_clusters"][frame]
        nc_rnd = trace["rnd"]["new_clusters"][frame]

        # place drivers near their old cluster (earning this slot if they stayed)
        # we add a deterministic jitter so they don't pile; seed on (frame, id) for stable look
        N = len(oc_rec)
        rng = np.random.default_rng(1000+frame)
        jitter_rec = _jitter(N)
        jitter_rnd = _jitter(N)

        xy_rec = pos[oc_rec] + jitter_rec
        xy_rnd = pos[oc_rnd] + jitter_rnd

        scat_rec.set_offsets(xy_rec)
        scat_rnd.set_offsets(xy_rnd)

        # draw arrows for movers (old->new)
        movers_rec = np.where(oc_rec != nc_rec)[0]
        movers_rnd = np.where(oc_rnd != nc_rnd)[0]
        for i in movers_rec:
            x0,y0 = pos[oc_rec[i]]
            x1,y1 = pos[nc_rec[i]]
            arr = ax_rec.arrow(x0, y0, (x1-x0)*0.85, (y1-y0)*0.85, width=0.005, head_width=0.06, alpha=0.6)
            arrows_rec.append(arr)
        for i in movers_rnd:
            x0,y0 = pos[oc_rnd[i]]
            x1,y1 = pos[nc_rnd[i]]
            arr = ax_rnd.arrow(x0, y0, (x1-x0)*0.85, (y1-y0)*0.85, width=0.005, head_width=0.06, alpha=0.6)
            arrows_rnd.append(arr)

        # texts
        dt = trace["dt"]
        text_rec.set_text(f"slot t={frame}  (h={frame*dt:.1f}–{(frame+1)*dt:.1f})\nRevenue this slot: {trace['rec']['slot_revenue'][frame]:.2f}")
        text_rnd.set_text(f"slot t={frame}  (h={frame*dt:.1f}–{(frame+1)*dt:.1f})\nRevenue this slot: {trace['rnd']['slot_revenue'][frame]:.2f}")
        return scat_rec, scat_rnd, text_rec, text_rnd, *arrows_rec, *arrows_rnd

    anim = FuncAnimation(fig, update, frames=T, interval=700, blit=False)
    plt.close(fig)  # prevent double display in Colab

    # Display inline (HTML5)
    from IPython.display import HTML
    display(HTML(anim.to_jshtml()))

    # Save files you can download / embed
    try:
        anim.save(save_mp4, writer='ffmpeg', dpi=160)
        print(f"Saved MP4: {save_mp4}")
    except Exception as e:
        print("MP4 save failed (missing ffmpeg?). Skipping MP4.", e)

    try:
        anim.save(save_gif, writer=PillowWriter(fps=1))
        print(f"Saved GIF: {save_gif}")
    except Exception as e:
        print("GIF save failed.", e)

    return anim
