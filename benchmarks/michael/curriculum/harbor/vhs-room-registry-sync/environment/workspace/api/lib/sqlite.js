/**
 * better-sqlite3-compatible facade over Node's built-in `node:sqlite` (DatabaseSync).
 *
 * The grader container has no npm registry, so db.js imports this module instead of
 * `better-sqlite3`. Supported: new Database(file), db.prepare(sql).run/get/all, db.exec,
 * db.pragma, db.transaction(fn), db.close. Like better-sqlite3, `undefined` parameters bind
 * as NULL. Read-only support file.
 */
import { DatabaseSync } from 'node:sqlite';

const bindable = (args) => args.map((value) => (value === undefined ? null : value));
const plain = (row) => (row ? { ...row } : row);

export default class Database {
  constructor(file) {
    this.name = file;
    this.handle = new DatabaseSync(file);
    this.inTransaction = false;
  }

  prepare(sql) {
    const statement = this.handle.prepare(sql);
    return {
      run: (...args) => statement.run(...bindable(args)),
      get: (...args) => plain(statement.get(...bindable(args))),
      all: (...args) => statement.all(...bindable(args)).map(plain),
    };
  }

  exec(sql) {
    this.handle.exec(sql);
    return this;
  }

  pragma(text) {
    return this.handle.prepare(`PRAGMA ${text}`).all().map(plain);
  }

  transaction(fn) {
    return (...args) => {
      if (this.inTransaction) return fn(...args);
      this.handle.exec('BEGIN');
      this.inTransaction = true;
      try {
        const result = fn(...args);
        this.handle.exec('COMMIT');
        return result;
      } catch (error) {
        this.handle.exec('ROLLBACK');
        throw error;
      } finally {
        this.inTransaction = false;
      }
    };
  }

  close() {
    this.handle.close();
  }
}
