// Copyright DB Netz AG and the capella-collab-manager contributors
// SPDX-License-Identifier: Apache-2.0

const { writeFileSync } = require('fs');
const util = require('node:util');
const exec = util.promisify(require('node:child_process').exec);

async function main() {
  const git = exec('git describe --tags');
  const gitTag = exec('git describe --tags --abbrev=0');

  const github = fetch(
    'https://api.github.com/repos/DSD-DBS/capella-collab-manager/releases'
  );

  const gitResponse = await git;
  console.error(gitResponse.stderr);
  let gitTagResponse = await gitTag;
  console.error(gitTagResponse.stderr);
  const response = await github;
  const data = await response.json();

  if (gitTagResponse.error || gitResponse.error || !response.ok) {
    process.exit(1);
  }

  const json = {
    github: data,
    git: {
      version: gitResponse.stdout.replace(/\n/g, ''),
      tag: gitTagResponse.stdout.replace(/\n/g, ''),
    },
  };

  writeFileSync('src/assets/version.json', JSON.stringify(json));
}

main();
