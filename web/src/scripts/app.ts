import topicQueries from '../data/topics';

type Article = {
  article_id: string;
  source_id: string;
  publisher_id?: string;
  source_name: string;
  language: string;
  title: string;
  summary_text: string;
  url: string;
  published_at: string | null;
  date_status: string;
  first_seen_at: string;
  matched_terms: string[];
};

type Snapshot = {
  state_version: string;
  generated_at: string;
  timezone: string;
  last_success_at: string | null;
  last_attempt_at: string;
  overall_status: string;
  articles: Article[];
  source_states: Array<{ source_id: string; publisher_id?: string; source_name?: string; status: string; accepted_count: number; consecutive_failures: number }>;
  stats: { article_count: number; new_count: number; updated_count: number; rejected_count: number };
};

type State = { query: string; range: string; source: string; language: string; topic: string; visible: number };

const root = document.querySelector<HTMLElement>('[data-app]');
if (root) {
  const bootstrap = JSON.parse(root.dataset.snapshot || '{}') as Snapshot;
  const nodes = {
    list: root.querySelector<HTMLElement>('[data-list]')!,
    focus: root.querySelector<HTMLElement>('[data-focus]')!,
    empty: root.querySelector<HTMLElement>('[data-empty]')!,
    count: root.querySelector<HTMLElement>('[data-count]')!,
    active: root.querySelector<HTMLElement>('[data-active-filters]')!,
    status: root.querySelector<HTMLElement>('[data-status]')!,
    statusLabel: root.querySelector<HTMLElement>('[data-status-label]')!,
    statusDetail: root.querySelector<HTMLElement>('[data-status-detail]')!,
    retry: root.querySelector<HTMLButtonElement>('[data-retry]')!,
    sources: root.querySelector<HTMLElement>('[data-sources]')!,
    languages: root.querySelector<HTMLElement>('[data-languages]')!,
    topics: root.querySelector<HTMLElement>('[data-topics]')!,
    search: root.querySelector<HTMLInputElement>('[data-search]')!,
    more: root.querySelector<HTMLButtonElement>('[data-load-more]')!,
    version: root.querySelector<HTMLElement>('[data-version]')!,
    heroDate: root.querySelector<HTMLElement>('[data-hero-date]')!,
    heroArticleCount: root.querySelector<HTMLElement>('[data-hero-article-count]')!,
    heroSourceCount: root.querySelector<HTMLElement>('[data-hero-source-count]')!,
    heroStatus: root.querySelector<HTMLElement>('[data-hero-status]')!,
    heroLastUpdate: root.querySelector<HTMLElement>('[data-hero-last-update]')!,
    heroSources: root.querySelector<HTMLElement>('[data-hero-sources]')!,
  };
  let snapshot = bootstrap;
  let snapshotError = false;
  let snapshotLoading = false;
  let state: State = readUrl();
  let searchTimer: number | undefined;

  function readUrl(): State {
    const params = new URLSearchParams(location.search);
    const validRanges = new Set(['all', 'today', '7d', 'unknown']);
    return {
      query: params.get('q') || '', range: validRanges.has(params.get('range') || '') ? params.get('range')! : 'all',
      source: params.get('source') || '', language: ['zh', 'en'].includes(params.get('lang') || '') ? params.get('lang')! : '',
      topic: ['大模型', 'Agent', 'AI 应用', '开发工具', '芯片与算力', '政策与安全', '研究'].includes(params.get('topic') || '') ? params.get('topic')! : '', visible: 20,
    };
  }

  function writeUrl(mode: 'push' | 'replace') {
    const params = new URLSearchParams();
    if (state.query) params.set('q', state.query);
    if (state.range !== 'all') params.set('range', state.range);
    if (state.source) params.set('source', state.source);
    if (state.language) params.set('lang', state.language);
    if (state.topic) params.set('topic', state.topic);
    const url = `${location.pathname}${params.toString() ? `?${params}` : ''}`;
    history[mode === 'push' ? 'pushState' : 'replaceState']({}, '', url);
  }

  function normalize(value: string) {
    return value.normalize('NFKC').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
  }

  function formatDate(value: string | null) {
    if (!value) return '发布时间未知';
    const date = new Date(value);
    return new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date);
  }

  function localDay(value: string | null) {
    if (!value) return null;
    return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai' }).format(new Date(value));
  }

  function todayKey() { return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai' }).format(new Date()); }

  function dateMatches(article: Article) {
    if (state.range === 'unknown') return !article.published_at;
    if (state.range === 'all') return true;
    const day = localDay(article.published_at);
    if (!day) return false;
    const now = new Date(`${todayKey()}T00:00:00+08:00`).getTime();
    const target = new Date(`${day}T00:00:00+08:00`).getTime();
    const difference = Math.floor((now - target) / 86400000);
    return state.range === 'today' ? difference === 0 : difference >= 0 && difference < 7;
  }

  function filteredArticles() {
    const queryTerms = normalize(state.query).split(' ').filter(Boolean);
    const topicTerms = state.topic ? (topicQueries[state.topic] || []) : [];
    const sourceIds = new Set(snapshot.articles.map((article) => article.source_id));
    if (state.source && !sourceIds.has(state.source)) state.source = '';
    return snapshot.articles.filter((article) => {
      if (state.source && article.source_id !== state.source) return false;
      if (state.language && article.language !== state.language) return false;
      if (!dateMatches(article)) return false;
      const haystack = normalize(`${article.title} ${article.summary_text} ${article.source_name} ${article.matched_terms.join(' ')}`);
      if (topicTerms.length && !topicTerms.some((term) => haystack.includes(normalize(term)))) return false;
      if (queryTerms.length && !queryTerms.every((term) => haystack.includes(term))) return false;
      return true;
    }).sort((a, b) => {
      const dateOrder = (left: Article, right: Article) => {
        if (Boolean(left.published_at) !== Boolean(right.published_at)) return left.published_at ? -1 : 1;
        return (right.published_at || right.first_seen_at || '').localeCompare(left.published_at || left.first_seen_at || '');
      };
      if (!state.query) return dateOrder(a, b);
      const score = (item: Article) => {
        const title = normalize(item.title); const source = normalize(item.source_name); const text = normalize(`${item.summary_text} ${item.matched_terms.join(' ')}`);
        return queryTerms.reduce((total, term) => total + (title.includes(term) ? 3 : 0) + (source.includes(term) ? 2 : 0) + (text.includes(term) ? 1 : 0), 0);
      };
      return score(b) - score(a) || dateOrder(a, b);
    });
  }

  function articleMarkup(article: Article, variant: 'main' | 'side' | 'list' = 'list', index = 0) {
    const card = document.createElement('article'); card.className = `article-item article-item-${variant}`;
    const indexNode = document.createElement('span'); indexNode.className = 'article-index'; indexNode.textContent = String(index + 1).padStart(2, '0');
    const meta = document.createElement('div');
    meta.className = 'article-meta';
    meta.setAttribute('aria-label', '文章元数据');
    const source = document.createElement('span');
    source.className = 'source';
    source.textContent = article.source_name;
    const language = document.createElement('span');
    language.className = 'lang';
    language.textContent = article.language === 'zh' ? '中文' : 'English';
    const time = document.createElement('time');
    time.className = 'time';
    time.dateTime = article.published_at || '';
    time.textContent = formatDate(article.published_at);
    meta.append(source, language, time);
    const title = document.createElement('h3'); title.textContent = article.title;
    const summary = document.createElement('p'); summary.textContent = article.summary_text || '来源未提供摘要。';
    const body = document.createElement('div'); body.className = 'article-body'; body.append(meta, title, summary);
    if (/^https?:\/\//i.test(article.url)) {
      const link = document.createElement('a'); link.className = 'article-link'; link.href = article.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = '查看原文';
      const arrow = document.createElement('span'); arrow.textContent = '↗'; link.append(' ', arrow);
      card.append(indexNode, body, link);
    } else {
      const missingLink = document.createElement('span'); missingLink.className = 'missing-link'; missingLink.textContent = '来源未提供链接';
      card.append(indexNode, body, missingLink);
    }
    return card;
  }

  function focusArticles() {
    const candidates = snapshot.articles.filter((article) => localDay(article.published_at) === todayKey());
    const pool = candidates.length ? candidates : snapshot.articles;
    const selected: Article[] = [];
    const seen = new Set<string>();
    for (const article of pool) {
      if (!seen.has(article.publisher_id || article.source_id)) {
        selected.push(article); seen.add(article.publisher_id || article.source_id);
      }
      if (selected.length === 3) break;
    }
    if (selected.length < 3) for (const article of pool) if (!selected.includes(article)) { selected.push(article); if (selected.length === 3) break; }
    return selected;
  }

  function renderFocus() {
    const selected = focusArticles();
    nodes.focus.classList.toggle('is-single', selected.length === 1);
    const main = selected[0] ? articleMarkup(selected[0], 'main', 0) : null;
    const side = document.createElement('div');
    side.className = 'focus-side';
    selected.slice(1).forEach((article, index) => side.append(articleMarkup(article, 'side', index + 1)));
    nodes.focus.replaceChildren(...([main, side].filter(Boolean) as HTMLElement[]));
  }

  function renderHero() {
    const publisherCount = new Set(snapshot.source_states.filter((source) => ['success', 'empty_feed'].includes(source.status)).map((source) => source.publisher_id || source.source_id)).size;
    nodes.heroArticleCount.textContent = String(snapshot.stats.article_count);
    nodes.heroSourceCount.textContent = String(publisherCount || new Set(snapshot.articles.map((article) => article.publisher_id || article.source_id)).size);
    nodes.heroDate.textContent = snapshot.last_attempt_at ? formatDate(snapshot.last_attempt_at) : '—';
    nodes.heroLastUpdate.textContent = snapshot.last_success_at ? `最近成功 ${formatDate(snapshot.last_success_at)}` : '尚无成功记录';
    const statusMap: Record<string, string> = { success: '已更新', no_new: '无新内容', partial_success: '部分更新', degraded: '降级', failed: '失败' };
    nodes.heroStatus.textContent = statusMap[snapshot.overall_status] || '读取中';
    const sources = [...new Map(snapshot.articles.map((article) => [article.source_id, article.source_name])).entries()];
    nodes.heroSources.replaceChildren(...sources.slice(0, 4).map(([id, name]) => { const item = document.createElement('span'); item.className = 'source-stamp'; item.textContent = `${name} · ${id.toUpperCase()}`; return item; }));
  }

  function renderSources() {
    const sources = [...new Map(snapshot.articles.map((article) => [article.source_id, article.source_name])).entries()];
    nodes.sources.replaceChildren(...sources.map(([id, name]) => {
      const button = document.createElement('button'); button.type = 'button'; button.className = state.source === id ? 'filter-chip is-active' : 'filter-chip'; button.textContent = name; button.onclick = () => { state.source = state.source === id ? '' : id; state.visible = 20; writeUrl('push'); render(); }; return button;
    }));
  }

  function renderLanguages() {
    nodes.languages.querySelectorAll<HTMLButtonElement>('[data-language]').forEach((button) => {
      button.classList.toggle('is-active', button.dataset.language === state.language);
      button.onclick = () => { state.language = state.language === button.dataset.language ? '' : (button.dataset.language || ''); state.visible = 20; writeUrl('push'); render(); };
    });
  }

  function renderTopics() {
    nodes.topics.replaceChildren(...Object.keys(topicQueries).map((topic) => { const button = document.createElement('button'); button.type = 'button'; button.className = state.topic === topic ? 'filter-chip is-active' : 'filter-chip'; button.textContent = topic; button.onclick = () => { state.topic = state.topic === topic ? '' : topic; state.visible = 20; writeUrl('push'); render(); }; return button; }));
  }

  function render() {
    nodes.search.value = state.query;
    document.querySelectorAll<HTMLButtonElement>('[data-range]').forEach((button) => button.classList.toggle('is-active', button.dataset.range === state.range));
    const articles = filteredArticles();
    const visible = articles.slice(0, state.visible);
    nodes.list.replaceChildren(...visible.map((article, index) => articleMarkup(article, 'list', index)));
    renderFocus();
    nodes.empty.hidden = articles.length !== 0;
    nodes.list.hidden = articles.length === 0;
    const hasMore = articles.length > state.visible;
    nodes.more.hidden = articles.length === 0;
    nodes.more.disabled = !hasMore;
    nodes.more.setAttribute('aria-disabled', String(!hasMore));
    nodes.more.firstChild!.textContent = hasMore ? '显示更多资讯 ' : '已显示全部资讯 ';
    nodes.count.textContent = `${articles.length} 条结果`;
    const filterText = [state.query && `“${state.query}”`, state.topic, state.source, state.range !== 'all' && state.range, state.language].filter(Boolean).join(' · ');
    nodes.active.textContent = filterText || '全部来源 · 最近更新优先';
    renderSources(); renderLanguages(); renderTopics(); renderHero();
  }

  function renderStatus() {
    const failures = snapshot.source_states.filter((source) => !['success', 'empty_feed'].includes(source.status));
    const lastSuccess = snapshot.last_success_at ? formatDate(snapshot.last_success_at) : '尚无成功记录';
    const stale = snapshot.last_success_at && Date.now() - new Date(snapshot.last_success_at).getTime() > 36 * 3600000;
    const isInitialRead = !snapshotError && snapshot.state_version === 'bootstrap' && snapshot.articles.length === 0;
    nodes.status.className = `status-strip ${failures.length || snapshotError ? 'is-warning' : ''} ${stale ? 'is-stale' : ''}`;
    nodes.statusLabel.textContent = snapshotLoading ? '正在读取最新数据' : isInitialRead ? '正在读取最新数据' : snapshotError ? '无法读取最新数据' : snapshot.overall_status === 'failed' ? '本次更新失败，已保留旧数据' : stale ? '数据可能已过期' : failures.length ? '部分来源更新失败' : snapshot.overall_status === 'no_new' ? '来源连接正常，暂无新内容' : '数据已更新';
    const sourceNames = failures.map((source) => snapshot.articles.find((article) => article.source_id === source.source_id)?.source_name || source.source_name || source.source_id);
    nodes.statusDetail.textContent = snapshotLoading ? '正在获取最新快照…' : snapshotError ? '请检查网络后重试；当前页面仍保留可用快照。' : `${snapshot.stats.article_count} 条资讯 · 最近成功 ${lastSuccess}${failures.length ? ` · 失败：${sourceNames.join('、')}` : ''}`;
    nodes.retry.hidden = !snapshotError && !snapshotLoading;
    nodes.retry.disabled = snapshotLoading;
    nodes.retry.textContent = snapshotLoading ? '读取中…' : '重试';
    nodes.version.textContent = `数据版本：${snapshot.state_version}`;
  }

  async function loadSnapshot() {
    if (snapshotLoading) return;
    snapshotLoading = true;
    renderStatus();
    try {
      const base = import.meta.env.BASE_URL.endsWith('/') ? import.meta.env.BASE_URL : `${import.meta.env.BASE_URL}/`;
      const response = await fetch(`${base}data/snapshot.json?ts=${Date.now()}`, { cache: 'no-store' });
      if (!response.ok) throw new Error('snapshot unavailable');
      snapshot = await response.json() as Snapshot;
      snapshotError = false;
    } catch { snapshotError = true; /* bootstrap keeps the first render usable */ }
    finally { snapshotLoading = false; }
    renderStatus(); render();
  }

  nodes.search.addEventListener('input', () => { state.query = nodes.search.value; state.visible = 20; window.clearTimeout(searchTimer); searchTimer = window.setTimeout(() => { writeUrl('replace'); render(); }, 150); });
  nodes.search.addEventListener('keydown', (event) => { if (event.key === 'Enter') { writeUrl('push'); render(); } });
  root.querySelectorAll<HTMLButtonElement>('[data-range]').forEach((button) => button.addEventListener('click', () => { state.range = button.dataset.range || 'all'; state.visible = 20; writeUrl('push'); render(); }));
  root.querySelectorAll<HTMLButtonElement>('[data-clear], [data-empty-clear]').forEach((button) => button.addEventListener('click', () => { state = { query: '', range: 'all', source: '', language: '', topic: '', visible: 20 }; writeUrl('push'); render(); }));
  nodes.more.addEventListener('click', () => { state.visible += 20; render(); });
  nodes.retry.addEventListener('click', () => { if (!snapshotLoading) { snapshotError = false; loadSnapshot(); } });
  window.addEventListener('popstate', () => { state = readUrl(); render(); });
  window.setInterval(() => { if (document.visibilityState === 'visible') loadSnapshot(); }, 5 * 60 * 1000);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') loadSnapshot(); });
  renderStatus(); render(); loadSnapshot();
}
