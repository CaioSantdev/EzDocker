/** Valida a resposta antes de tentar interpretá-la como JSON. */
export async function request<T>(path: string, method = 'GET', signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers: { Accept: 'application/json' },
      signal: AbortSignal.any([AbortSignal.timeout(120000), ...(signal ? [signal] : [])]),
    });
  } catch {
    throw new Error('Não foi possível receber a resposta da API. Verifique o backend e consulte o estado antes de repetir uma ação.');
  }
  const contentType = response.headers.get('content-type')?.split(';')[0].trim().toLowerCase() || '';
  if (contentType !== 'application/json' && !contentType.endsWith('+json')) {
    if (!response.ok) {
      throw new Error(`A API está indisponível (HTTP ${response.status}). Verifique se o backend está rodando na porta 18080.`);
    }
    throw new Error('O servidor retornou uma página HTML ou texto no lugar da API. Abra o painel em http://127.0.0.1:18081 e verifique o proxy /api para a porta 18080.');
  }
  let data;
  try { data = await response.json(); }
  catch { throw new Error('A API retornou uma resposta JSON inválida. Tente atualizar novamente.'); }
  if (!response.ok) {
    throw new Error(typeof data?.message === 'string' ? data.message : `A API retornou erro ${response.status}.`);
  }
  return data as T;
}
