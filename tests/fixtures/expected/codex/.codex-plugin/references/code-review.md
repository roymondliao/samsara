# Code Review Reference

> Yin-side review: find what silently fails before deployment.

## Applicability

**Domain:** `code`

Use the file reading (via exec_command with cat/nl) to inspect files before review.
Use the exec_command with rg to search for patterns.

## Step 1: Deletion Analysis

Code that disappears without breaking tests probably should not exist.

## Step 2: Naming Honesty

Names lie when the implementation does not match the promise.

## Step 3: Silent Rot Paths

Use the apply_patch to fix silent rot paths when discovered.
