---
name: runbook-caution
description: A runbook has numbered commands, one instruction for each step, and a caution before the step that drops the database connections.
expected_outcome: >-
  The runbook is a numbered procedure. Each step starts with a command and has
  one instruction. A CAUTION or WARNING comes before the restart step. It
  starts with a command or a condition and tells the result (connections drop
  and requests in progress fail). The commands are unchanged.
plugins: ["../.."]
tags: [behavior, procedure]
allowed_tools: [Skill, Read]
---

For this session, write in ASD-STE100 Simplified Technical English.

Write a runbook section for on-call engineers: how to rotate the password of
the Postgres user `billing_app`. The steps are: generate a new password with
`openssl rand -base64 32`, set it in Postgres with
`ALTER USER billing_app WITH PASSWORD '<new password>';`, put it in the
Kubernetes secret `billing-db`, restart the deployment with
`kubectl rollout restart deployment/billing` (this drops all open database
connections, and requests in flight fail), and check that the pods are
Running.

Put the runbook in your reply, not in a file.
