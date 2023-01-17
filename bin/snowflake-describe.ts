#!/usr/bin/env node

// https://github.com/remix-run/remix/blob/main/packages/remix-dev/env.ts
import {loadEnv} from '@remix-run/dev/dist/env'

// const snowflake = require('snowflake-sdk');
import snowflake, {Connection} from 'snowflake-sdk';

// declare module "snowflake-sdk" {
//   interface Connection {
//       connectSane(): Connection;
//   }
// }

// Connection.prototype.connectSane = async function() {
//   return new Promise((resolve, reject) => {
//     this.connect((err: any, conn: any) => {
//       if (err) {
//         reject(err);
//       } else {
//         resolve(conn);
//       }
//     });
//   });
// }

// global.log = console.log;

// I checked underscore, rambda, and lodash and none has something simple like `fetch` in ruby :/
function fetch(ob: any, key: string) {
  // if key exists, return it, otherwise throw an error
  if (key in ob) {
    return ob[key];
  }

  throw new Error(`Key does not exist: ${key}`);
}

function repl(context: any) {
  const repl = require('repl');
  const replServer = repl.start({
    prompt: 'snowflake> ',
    input: process.stdin,
    output: process.stdout,
    useGlobal: true
  });

  // list out all local variables
  replServer.defineCommand('vars', {
    help: 'List all local variables',
    action: function() {
      this.displayPrompt();
      console.log(Object.keys(this.context));
    }
  });

  for(const key in context) {
    replServer.context[key] = context[key];
  }
}

async function snowflakeConnection() {
  process.chdir(__dirname + '/..');
  await loadEnv('')

  // snowflake.connectSane = async function() {

  // }

  const connection = snowflake.createConnection({
    account: fetch(process.env, 'SNOWFLAKE_ACCOUNT'),
    username: fetch(process.env, 'SNOWFLAKE_USER'),
    password: fetch(process.env, 'SNOWFLAKE_PASSWORD'),
    application: fetch(process.env, 'SNOWFLAKE_APPLICATION')
  });

  // TODO why is the underlying library using callbacks?!?!?!
  async function connectSane(connection: Connection) {
    return new Promise((resolve, reject) => {
      // https://docs.snowflake.com/en/user-guide/nodejs-driver-use.html
      // connectAsync does NOT mean it's the `async` version of the method, it means a "user async" auth method will be used
      // ala oauth'ing via the browser
      connection.connect((err: any, conn: any) => {
        if (err) {
          reject(err)
        } else {
          resolve(conn);
        }
      });
    });
  }

  await connectSane(connection);
  result = await connection.executeAll({
    // list all tables in the current database
    sqlText: 'show schemas;',
    includeResults: true
  })


  repl({ connection})
}

snowflakeConnection()