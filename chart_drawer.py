import matplotlib.pyplot as plt
import matplotlib
from collections import Counter
from movie_repository import MovieRepository  # 从同目录导入

class ChartDrawer:
    def __init__(self, repo: MovieRepository):
        self.repo = repo
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False

    def draw(self, save_path='douban.png'):
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('豆瓣 Top 100 数据分析', fontsize=18)
        self._draw_ratings(axes[0, 0])
        self._draw_decades(axes[0, 1])
        self._draw_genres(axes[1, 0])
        self._draw_countries(axes[1, 1])
        plt.tight_layout()
        plt.savefig(save_path)
        print(f"图表已保存为 {save_path}")
        plt.show()

    def _draw_ratings(self, ax):
        ax.hist(self.repo.get_ratings(), bins=10, color='steelblue', edgecolor='white')
        ax.set_title('① 评分分布')
        ax.set_xlabel('评分')
        ax.set_ylabel('数量')

    def _draw_decades(self, ax):
        decade = Counter((y // 10) * 10 for y in self.repo.get_years())
        decades_sorted = sorted(decade.keys())
        ax.bar([f"{d}s" for d in decades_sorted],
               [decade[d] for d in decades_sorted], color='coral', edgecolor='white')
        ax.set_title('② 年代分布')

    def _draw_genres(self, ax):
        top10 = Counter(self.repo.get_genres()).most_common(10)
        ax.barh([k for k, _ in top10], [v for _, v in top10], color='mediumseagreen')
        ax.set_title('③ 类型 TOP10')

    def _draw_countries(self, ax):
        cty = Counter(self.repo.get_countries())
        top_cty = {k: v for k, v in cty.items() if v >= 3}
        other = sum(v for v in cty.values() if v < 3)
        if other > 0:
            top_cty['其他'] = other
        ax.pie(top_cty.values(), labels=top_cty.keys(),
               autopct='%1.1f%%', colors=plt.cm.Pastel1.colors)
        ax.set_title('④ 国家/地区占比')