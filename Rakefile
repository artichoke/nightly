# frozen_string_literal: true

require 'fileutils'
require 'open-uri'
require 'shellwords'
require 'bundler/audit/task'
require 'rubocop/rake_task'

task default: %i[format lint]

desc 'Lint sources'
task lint: %i[lint:python lint:rubocop:autocorrect]

namespace :lint do
  RuboCop::RakeTask.new(:rubocop)

  desc 'Lint Python files with ruff'
  task python: :'venv:create' do
    sh 'venv/bin/mypy .'
    sh 'venv/bin/ruff check .'
  end
end

desc 'Format sources'
task format: %i[format:python format:text]

namespace :format do
  desc 'Format Python files with black and ruff'
  task python: :'venv:create' do
    sh 'venv/bin/black .'
    sh 'venv/bin/ruff check --fix .'
  end

  desc 'Format text, YAML, and Markdown sources with prettier'
  task :text do
    sh 'npm run fmt'
  end
end

desc 'Format sources'
task fmt: %i[fmt:python fmt:text]

namespace :fmt do
  desc 'Format Python files with black and ruff'
  task python: :'venv:create' do
    sh 'venv/bin/black .'
    sh 'venv/bin/ruff check --fix .'
  end

  desc 'Format text, YAML, and Markdown sources with prettier'
  task :text do
    sh 'npm run fmt'
  end
end

Bundler::Audit::Task.new

namespace :venv do
  desc 'Create a new virtualenv with the pinned requirements'
  task :create do
    next if File.exist?('venv/bin/black') && File.exist?('venv/bin/mypy') && File.exist?('venv/bin/ruff')

    sh 'python3 -m venv --upgrade-deps venv'
    sh 'venv/bin/python3 -m pip install --upgrade wheel pip-tools'
    sh 'venv/bin/python3 -m pip install --require-hashes --upgrade -r requirements.txt -r dev-requirements.txt'
  end

  desc 'Remove the venv'
  task :clean do
    FileUtils.remove_dir('venv', true)
  end

  desc 'Pin dependencies to requirements.txt'
  task :pin do
    Rake::Task['venv:create'].invoke unless File.exist?('venv/bin/pip-compile')

    FileUtils.remove_file('requirements.txt', true)
    FileUtils.remove_file('dev-requirements.txt', true)
    sh 'venv/bin/python3 -m piptools compile --generate-hashes --output-file requirements.txt pyproject.toml'
    sh 'venv/bin/python3 -m piptools compile --generate-hashes --output-file dev-requirements.txt --extra dev pyproject.toml'
  end
end
