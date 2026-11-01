import { test } from 'node:test';
import assert from 'node:assert/strict';
import { request } from '../src/api-client.ts';

test('HTML com HTTP 200 produz orientação sobre proxy sem erro de parse', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response('<!doctype html><html></html>', {
    headers: { 'content-type': 'text/html' },
  }));
  await assert.rejects(request('/containers'), /proxy \/api/);
});

test('falha de proxy sem JSON informa indisponibilidade', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response('', { status: 502 }));
  await assert.rejects(request('/containers'), /indisponível \(HTTP 502\)/);
});

test('JSON válido é retornado e mensagem de erro da API é preservada', async t => {
  t.mock.method(globalThis, 'fetch', async () => Response.json([{ id: 'abc' }]));
  assert.deepEqual(await request('/containers'), [{ id: 'abc' }]);
  globalThis.fetch = async () => Response.json({ message: 'Docker desligado' }, { status: 503 });
  await assert.rejects(request('/containers'), /Docker desligado/);
});

test('conteúdo JSON inválido não expõe SyntaxError ao usuário', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response('<!doctype html>', {
    headers: { 'content-type': 'application/json' },
  }));
  await assert.rejects(request('/containers'), /resposta JSON inválida/);
});
