import { test } from 'node:test';
import assert from 'node:assert/strict';
import { LogPoller } from '../src/log-poller.ts';

const flush = async () => { await Promise.resolve(); await Promise.resolve(); };

test('consultas do mesmo painel não se sobrepõem e retomam após resposta', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  let resolve;
  let calls = 0;
  const values = [];
  const poller = new LogPoller(() => {
    calls++;
    return new Promise(done => { resolve = done; });
  }, value => values.push(value), assert.fail);
  poller.start();
  poller.start();
  t.mock.timers.tick(10000);
  assert.equal(calls, 1);
  resolve('primeira saída');
  await flush();
  assert.deepEqual(values, ['primeira saída']);
  t.mock.timers.tick(2000);
  assert.equal(calls, 2);
  poller.pause();
});

test('pausa cancela a requisição e descarta resposta atrasada', async () => {
  let signal;
  let resolve;
  const values = [];
  const poller = new LogPoller(current => {
    signal = current;
    return new Promise(done => { resolve = done; });
  }, value => values.push(value), assert.fail);
  poller.start();
  poller.pause();
  assert.equal(signal.aborted, true);
  resolve('resposta antiga');
  await flush();
  assert.deepEqual(values, []);
});

test('falha de um painel não bloqueia os outros e permite recuperação', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const values = [];
  const errors = [];
  let first = true;
  const failed = new LogPoller(async () => {
    if (first) { first = false; throw new Error('offline'); }
    return 'recuperado';
  }, value => values.push(value), error => errors.push(error.message));
  const healthy = new LogPoller(async () => 'outra aplicação', value => values.push(value), assert.fail);
  const slow = new LogPoller(() => new Promise(() => {}), assert.fail, assert.fail);
  failed.start(); healthy.start(); slow.start();
  await flush();
  assert.deepEqual(errors, ['offline']);
  assert.deepEqual(values, ['outra aplicação']);
  t.mock.timers.tick(2000);
  await flush();
  assert.ok(values.includes('recuperado'));
  failed.pause(); healthy.pause(); slow.pause();
});

test('retomada não aceita resposta de uma geração cancelada', async () => {
  const resolvers = [];
  const values = [];
  const poller = new LogPoller(() => new Promise(done => resolvers.push(done)), value => values.push(value), assert.fail);
  poller.start(); poller.pause(); poller.start();
  resolvers[0]('antigo');
  resolvers[1]('atual');
  await flush();
  assert.deepEqual(values, ['atual']);
  poller.pause();
});
