import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const apiErrorSource = readFileSync(
  new URL('../src/services/apiError.ts', import.meta.url),
  'utf8',
);

const loadHelper = async () => {
  const ts = await import('typescript');
  const source = ts.transpileModule(apiErrorSource, {
    compilerOptions: {
      module: ts.ModuleKind.ES2022,
      target: ts.ScriptTarget.ES2022,
      verbatimModuleSyntax: true,
    },
  }).outputText;
  const encoded = Buffer.from(source, 'utf8').toString('base64');
  return import(`data:text/javascript;base64,${encoded}`);
};

test('api error helper recognizes backend response shapes', () => {
  assert.match(apiErrorSource, /getApiErrorMessage/);
  assert.match(apiErrorSource, /data\.error/);
  assert.match(apiErrorSource, /data\.detail/);
  assert.match(apiErrorSource, /ECONNABORTED/);
  assert.match(apiErrorSource, /STATUS_MESSAGES/);
});

test('api error helper formats structured app errors', async () => {
  const { getApiErrorMessage } = await loadHelper();
  const message = getApiErrorMessage({
    response: { data: { error: { message: '删除失败：仍有关联数据' } } },
  }, { fallback: '删除失败' });
  assert.equal(message, '删除失败：仍有关联数据');
});

test('api error helper summarizes validation detail arrays', async () => {
  const { getApiErrorMessage } = await loadHelper();
  const message = getApiErrorMessage({
    response: {
      status: 422,
      data: { detail: [{ loc: ['body', 'email'], msg: '邮箱格式不正确' }] },
    },
  }, { action: '保存失败' });
  assert.equal(message, '保存失败：邮箱格式不正确');
});

test('api error helper handles timeout, network, and status fallbacks', async () => {
  const { getApiErrorMessage } = await loadHelper();
  assert.equal(getApiErrorMessage({ code: 'ECONNABORTED' }), '请求超时，请稍后重试');
  assert.equal(
    getApiErrorMessage({ message: 'Network Error' }, { action: '加载失败' }),
    '加载失败：网络连接失败，请检查服务是否可用后重试',
  );
  assert.equal(
    getApiErrorMessage({ response: { status: 403, data: {} } }),
    '当前账号没有权限执行此操作',
  );
});

test('api error helper formats fetch status errors', async () => {
  const { getHttpErrorMessage } = await loadHelper();
  assert.equal(
    getHttpErrorMessage(502, { detail: '模型服务暂时不可用' }, { action: '发送失败' }),
    '发送失败：模型服务暂时不可用',
  );
  assert.equal(getHttpErrorMessage(504), '请求超时，请稍后重试');
});
