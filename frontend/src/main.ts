import './style.css';
import { request } from './api-client';
import { LogPoller } from './log-poller';

type Container = { id: string; name: string; image: string; status: string };
type Action = 'start' | 'stop' | 'restart';
type Icon = Action | 'logs' | 'trash' | 'containers' | 'volumes';
const iconPaths: Record<Icon, string> = {
  containers: '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="14" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 17.5h.01M11 7.5h6M11 17.5h6"/>',
  volumes: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
  start: '<path d="m8 5 11 7-11 7Z"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="1"/>',
  restart: '<path d="M20 7v5h-5M20 12a8 8 0 1 0-2 5M20 7l-3-3"/>',
  logs: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
  trash: '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/>',
};

function icon(name: Icon): SVGSVGElement {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor');
  svg.setAttribute('stroke-width', '1.7');
  svg.setAttribute('stroke-linecap', 'round');
  svg.setAttribute('stroke-linejoin', 'round');
  svg.setAttribute('aria-hidden', 'true');
  svg.innerHTML = iconPaths[name];
  return svg;
}
const element = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const rows = element<HTMLTableSectionElement>('rows');
const search = element<HTMLInputElement>('search');
const refresh = element<HTMLButtonElement>('refresh');
let containers: Container[] = [];
let loading = false;
let loaded = false;
let pending = new Set<string>();

function notice(message: string, error = false) {
  const box = element('notice');
  box.textContent = message;
  box.hidden = !message;
  box.className = error ? 'notice error' : 'notice';
}

function cell(text: string, className = '') {
  const td = document.createElement('td');
  td.textContent = text;
  td.className = className;
  return td;
}

function render() {
  const query = search.value.trim().toLowerCase();
  const filtered = containers.filter(c => `${c.name} ${c.image}`.toLowerCase().includes(query));
  rows.replaceChildren();
  for (const container of filtered) {
    const row = document.createElement('tr');
    const name = cell('', 'container-name');
    const title = document.createElement('strong');
    title.textContent = container.name;
    const id = document.createElement('small');
    id.textContent = container.id;
    name.append(title, id);
    const status = cell('');
    const badge = document.createElement('span');
    badge.className = `badge ${container.status === 'running' ? 'running' : 'inactive'}`;
    badge.textContent = container.status;
    status.append(badge);
    const actions = cell('', 'actions');
    const options: [string, Action | 'logs' | 'trash'][] = [
      [container.status === 'running' ? 'Parar' : 'Iniciar', container.status === 'running' ? 'stop' : 'start'],
      ['Reiniciar', 'restart'], ['Logs', 'logs'], ['Excluir (em breve)', 'trash'],
    ];
    for (const [label, action] of options) {
      const button = document.createElement('button');
      button.className = `icon-button icon-${action}`;
      button.append(icon(action));
      button.disabled = pending.has(container.id) || action === 'trash';
      button.title = action === 'trash' ? 'Excluir: disponível em uma próxima etapa' : label;
      button.setAttribute('aria-busy', String(pending.has(container.id) && action !== 'trash'));
      button.setAttribute('aria-label', `${label}: ${container.name}`);
      if (action !== 'trash') {
        button.addEventListener('click', () => action === 'logs' ? openLogs(container) : runAction(container, action));
      }
      actions.append(button);
    }
    row.append(name, cell(container.image, 'image-name'), status, actions);
    rows.append(row);
  }
  const empty = element('empty');
  empty.hidden = filtered.length > 0;
  empty.textContent = loading ? 'Consultando containers…' : !loaded ? 'Não foi possível carregar os containers. Tente atualizar.' : containers.length ? 'Nenhum resultado para esta busca.' : 'Nenhum container encontrado neste Docker.';
  element('total').textContent = loaded ? String(containers.length) : '—';
  element('running').textContent = loaded ? String(containers.filter(c => c.status === 'running').length) : '—';
  element('stopped').textContent = loaded ? String(containers.filter(c => ['exited', 'created', 'dead'].includes(c.status)).length) : '—';
  element('nav-count').textContent = loaded ? String(containers.length) : '—';
  element('result-count').textContent = loaded ? String(filtered.length) : '';
  syncLogContainers();
}

const logContainer = element<HTMLSelectElement>('log-container');
const livePanels = new Map<string, { poller: LogPoller; paused: boolean; status: HTMLElement }>();

function syncLogContainers() {
  const previous = logContainer.value;
  const placeholder = new Option(loaded && !containers.length ? 'Nenhum container disponível' : 'Selecione um container', '');
  logContainer.replaceChildren(placeholder, ...containers.filter(c => !livePanels.has(c.id)).map(c => new Option(c.name, c.id)));
  if (containers.some(c => c.id === previous)) logContainer.value = previous;
}

function changeView() {
  const requested = location.hash.slice(1);
  const view = ['containers', 'volumes', 'logs'].includes(requested) ? requested : 'containers';
  for (const name of ['containers', 'volumes', 'logs']) {
    element(`view-${name}`).hidden = name !== view;
  }
  document.querySelectorAll<HTMLAnchorElement>('[data-view]').forEach(link => {
    if (link.dataset.view === view) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  const title = { containers: 'Containers', volumes: 'Volumes', logs: 'Logs' }[view]!;
  element('page-title').textContent = title;
  document.title = `EzDocker — ${title}`;
  element('page-description').textContent = {
    containers: 'Acompanhe seus serviços e gerencie cada execução.',
    volumes: 'O espaço dos dados persistentes do seu ambiente.',
    logs: 'Veja o que acontece por dentro dos seus serviços.',
  }[view]!;
  refresh.hidden = view === 'volumes';
  syncLivePolling();
}

function syncLivePolling() {
  const visible = !element('view-logs').hidden && !document.hidden;
  for (const panel of livePanels.values()) {
    if (visible && !panel.paused) panel.poller.start();
    else panel.poller.pause();
    if (panel.paused || !visible) panel.status.textContent = panel.paused ? 'Pausado' : 'Em espera · aba oculta';
  }
}

function addLogPanel(container: Container) {
  if (livePanels.has(container.id)) return;
  if (livePanels.size >= 3) { notice('Você pode acompanhar até 3 aplicações. Remova um painel para adicionar outra.', true); return; }
  const tail = element<HTMLInputElement>('page-tail');
  if (!tail.reportValidity()) return;
  const lineCount = tail.value;
  const card = document.createElement('article');
  card.className = 'live-log-card';
  const heading = document.createElement('div');
  heading.className = 'live-log-heading';
  const name = document.createElement('h3');
  name.textContent = container.name;
  const status = document.createElement('span');
  status.className = 'live-log-status';
  status.setAttribute('role', 'status');
  const output = document.createElement('pre');
  output.tabIndex = 0;
  output.setAttribute('aria-label', `Logs de ${container.name}`);
  output.textContent = 'Conectando…';
  const controls = document.createElement('div');
  controls.className = 'live-log-controls';
  const pause = document.createElement('button');
  pause.textContent = 'Pausar';
  pause.setAttribute('aria-label', `Pausar logs de ${container.name}`);
  const remove = document.createElement('button');
  remove.textContent = '✕';
  remove.title = 'Remover painel';
  remove.setAttribute('aria-label', `Remover painel de ${container.name}`);
  const autoLabel = document.createElement('label');
  const autoScroll = document.createElement('input');
  autoScroll.type = 'checkbox';
  autoScroll.checked = true;
  autoLabel.append(autoScroll, ' Seguir saída');
  controls.append(autoLabel, pause, remove);
  heading.append(name, controls);
  card.append(heading, status, output);
  const poller = new LogPoller(
    async signal => (await request<{ logs: string }>(`/containers/${encodeURIComponent(container.id)}/logs?tail=${lineCount}`, 'GET', signal)).logs,
    logs => {
      if (output.textContent !== (logs || 'Nenhum log disponível.')) output.textContent = logs || 'Nenhum log disponível.';
      if (autoScroll.checked) output.scrollTop = output.scrollHeight;
      status.textContent = `Ao vivo · ${lineCount} linhas · ${new Date().toLocaleTimeString('pt-BR')}`;
      status.classList.remove('log-error');
    },
    error => {
      status.textContent = `${(error as Error).message} Nova tentativa automática em 2s.`;
      status.classList.add('log-error');
    },
  );
  const panel = { poller, paused: false, status };
  livePanels.set(container.id, panel);
  pause.addEventListener('click', () => {
    panel.paused = !panel.paused;
    pause.textContent = panel.paused ? 'Retomar' : 'Pausar';
    pause.setAttribute('aria-label', `${panel.paused ? 'Retomar' : 'Pausar'} logs de ${container.name}`);
    syncLivePolling();
  });
  remove.addEventListener('click', () => {
    poller.pause();
    livePanels.delete(container.id);
    card.remove();
    updateLogLayout();
    syncLogContainers();
  });
  element('live-log-grid').append(card);
  notice('');
  updateLogLayout();
  syncLogContainers();
  syncLivePolling();
}

function updateLogLayout() {
  element('live-log-grid').dataset.count = String(livePanels.size);
  element('live-logs-empty').hidden = livePanels.size > 0;
  element<HTMLButtonElement>('add-log-panel').disabled = livePanels.size >= 3;
  element('live-panel-count').textContent = `${livePanels.size}/3 aplicações`;
}

async function load() {
  if (loading) return;
  loading = true;
  refresh.disabled = true;
  render();
  try {
    containers = await request<Container[]>('/containers');
    loaded = true;
    element('updated').textContent = `Atualizado às ${new Date().toLocaleTimeString('pt-BR')}`;
  } finally {
    loading = false;
    refresh.disabled = false;
    render();
  }
}

async function refreshList() {
  notice('');
  try { await load(); } catch (error) { notice((error as Error).message + (loaded ? ' Os dados exibidos são da última consulta.' : ''), true); }
}

async function runAction(container: Container, action: Action) {
  if (action !== 'start' && !window.confirm(`${action === 'stop' ? 'Parar' : 'Reiniciar'} o container “${container.name}”? Isso interrompe o serviço.`)) return;
  pending.add(container.id);
  render();
  notice('');
  try {
    const result = await request<Container>(`/containers/${encodeURIComponent(container.id)}/${action}`, 'POST');
    containers = containers.map(c => c.id === container.id ? result : c);
    notice(`Operação concluída em ${container.name}. Estado: ${result.status}.`);
    try { await load(); } catch { notice('A ação foi concluída, mas a atualização da lista falhou. Clique em Atualizar.', true); }
  } catch (error) { notice((error as Error).message, true); }
  finally { pending.delete(container.id); render(); }
}

function openLogs(container: Container) {
  location.hash = 'logs';
  changeView();
  addLogPanel(container);
}

search.addEventListener('input', render);
refresh.addEventListener('click', refreshList);
element<HTMLFormElement>('page-logs-form').addEventListener('submit', event => {
  event.preventDefault();
  const container = containers.find(c => c.id === logContainer.value);
  if (container) addLogPanel(container);
});
document.addEventListener('visibilitychange', syncLivePolling);
window.addEventListener('pagehide', () => { for (const panel of livePanels.values()) panel.poller.pause(); });
window.addEventListener('pageshow', syncLivePolling);
document.querySelectorAll<HTMLElement>('[data-nav-icon]').forEach(target => target.append(icon(target.dataset.navIcon as Icon)));
element('volume-symbol').append(icon('volumes'));
window.addEventListener('hashchange', changeView);
changeView();
void refreshList();
