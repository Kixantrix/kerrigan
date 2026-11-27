/**
 * Vendored, dependency-free subset of the Express 4 API used by this service.
 *
 * The grader container has no npm registry, so the API imports this module instead of
 * `express`. Supported: express(), express.Router(), express.json(), app/router .use/.get/
 * .post/.put/.delete with `:param` segments, mounted routers, error middleware (4 args),
 * req.get/params/query/body/path, res.status/json/send/set, app.listen. Read-only support file.
 */
import http from 'node:http';

function compile(pattern, prefix) {
  const keys = [];
  const body = pattern
    .replace(/\/+$/, '')
    .split('/')
    .map((part) => {
      if (part.startsWith(':')) {
        keys.push(part.slice(1));
        return '([^/]+)';
      }
      return part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    })
    .join('/');
  const regex = new RegExp(`^${body}${prefix ? '(?=/|$)' : '/?$'}`, 'i');
  return { regex, keys };
}

function createRouter() {
  const stack = [];

  function add(method, path, prefix, fns) {
    const { regex, keys } = compile(path, prefix);
    for (const fn of fns.flat()) stack.push({ method, path, prefix, regex, keys, fn });
  }

  function router(req, res, done) {
    router.handle(req, res, done);
  }

  router.handle = (req, res, done) => {
    let index = 0;
    const originalUrl = req.url;
    const next = (err) => {
      req.url = originalUrl;
      const layer = stack[index++];
      if (!layer) return done(err);
      const path = req.url.split('?')[0];
      const match = layer.regex.exec(path);
      if (!match) return next(err);
      if (layer.method && layer.method !== req.method) return next(err);
      const isErrorHandler = layer.fn.length === 4;
      if (err && !isErrorHandler) return next(err);
      if (!err && isErrorHandler) return next();
      req.params = { ...(req.params || {}) };
      layer.keys.forEach((key, i) => { req.params[key] = decodeURIComponent(match[i + 1]); });
      if (layer.prefix && layer.path !== '/') {
        const rest = req.url.slice(match[0].length) || '/';
        req.url = rest.startsWith('/') ? rest : `/${rest}`;
      }
      req.path = req.url.split('?')[0];
      try {
        const result = err ? layer.fn(err, req, res, next) : layer.fn(req, res, next);
        if (result && typeof result.catch === 'function') result.catch(next);
      } catch (error) {
        next(error);
      }
    };
    next();
  };

  router.use = (...args) => {
    const path = typeof args[0] === 'string' ? args.shift() : '/';
    add(null, path, true, args);
    return router;
  };
  for (const method of ['get', 'post', 'put', 'delete', 'patch']) {
    router[method] = (path, ...fns) => {
      add(method.toUpperCase(), path, false, fns);
      return router;
    };
  }
  return router;
}

function decorate(req, res) {
  const url = new URL(req.url, 'http://localhost');
  req.originalUrl = req.url;
  req.path = url.pathname;
  req.query = Object.fromEntries(url.searchParams);
  req.params = {};
  req.get = (name) => {
    const value = req.headers[String(name).toLowerCase()];
    return Array.isArray(value) ? value.join(', ') : value;
  };
  req.ip = req.socket?.remoteAddress;
  res.status = (code) => {
    res.statusCode = code;
    return res;
  };
  res.set = (name, value) => {
    res.setHeader(name, value);
    return res;
  };
  res.json = (value) => {
    if (!res.getHeader('content-type')) res.setHeader('content-type', 'application/json; charset=utf-8');
    res.end(JSON.stringify(value));
    return res;
  };
  res.send = (value) => {
    if (value !== null && typeof value === 'object' && !Buffer.isBuffer(value)) return res.json(value);
    if (!res.getHeader('content-type')) res.setHeader('content-type', 'text/html; charset=utf-8');
    res.end(value === undefined ? '' : value);
    return res;
  };
}

export default function express() {
  const router = createRouter();
  const app = (req, res) => {
    decorate(req, res);
    router.handle(req, res, (err) => {
      if (res.writableEnded) return;
      if (err) {
        res.statusCode = err.status || err.statusCode || 500;
        res.setHeader('content-type', 'text/plain; charset=utf-8');
        res.end(res.statusCode >= 500 ? 'Internal Server Error' : String(err.message || 'Error'));
        return;
      }
      res.statusCode = 404;
      res.setHeader('content-type', 'text/html; charset=utf-8');
      res.end(`Cannot ${req.method} ${req.path}`);
    });
  };
  for (const key of ['use', 'get', 'post', 'put', 'delete', 'patch', 'handle']) app[key] = router[key];
  app.listen = (...args) => http.createServer(app).listen(...args);
  return app;
}

express.Router = createRouter;

express.json = ({ limit = 1024 * 1024 } = {}) => (req, res, next) => {
  if (req.body !== undefined) return next();
  const type = String(req.headers['content-type'] || '');
  if (!type.includes('json')) {
    req.body = {};
    return next();
  }
  const chunks = [];
  let size = 0;
  req.on('data', (chunk) => {
    size += chunk.length;
    if (size <= limit) chunks.push(chunk);
  });
  req.on('error', next);
  req.on('end', () => {
    if (size > limit) {
      const error = new Error('request entity too large');
      error.status = 413;
      return next(error);
    }
    const text = Buffer.concat(chunks).toString('utf8');
    if (!text.trim()) {
      req.body = {};
      return next();
    }
    try {
      req.body = JSON.parse(text);
    } catch {
      const error = new Error('invalid JSON body');
      error.status = 400;
      return next(error);
    }
    next();
  });
};
