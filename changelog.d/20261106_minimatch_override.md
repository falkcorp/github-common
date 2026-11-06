### Security

#### `package.json`: `minimatch` 11 for `@typescript-eslint/typescript-estree`

Dependabot alert 52 (`minimatch` >= 7.0.0, < 11.0.1, medium) could not be fixed
by Dependabot: the newest `@typescript-eslint/typescript-estree` (8.72.1) still
requires `minimatch ^10.2.2`, so every security-update run ended with
`security_update_not_possible`. A scoped override pins that one dependency to
`^11.0.1` (resolves to 11.0.5). ESLint's own `minimatch ^3.1.5` is outside the
advisory range and is left alone; a global override would have moved it to an
incompatible major.
