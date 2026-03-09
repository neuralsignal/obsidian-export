# Profile Management

Profiles are YAML config files stored in `~/.obsidian-export/profiles/`. They let you save and reuse conversion settings for different output styles.

## Initialize

Create the directory structure and default profile:

```bash
obsidian-export init
```

This creates:

```
~/.obsidian-export/
  profiles/
    default.yaml
  styles/
```

## Create a Profile

```bash
# Create a new profile (starts from defaults)
obsidian-export profile create my_brand

# Create from an existing YAML config
obsidian-export profile create my_brand --from existing_config.yaml
```

## List Profiles

```bash
obsidian-export profile list
```

## Show Profile Contents

```bash
obsidian-export profile show my_brand
```

## Delete a Profile

```bash
obsidian-export profile delete my_brand --yes
```

## Using a Profile

Pass the profile name to the `convert` command:

```bash
obsidian-export convert --input my_note.md --format pdf --output my_note.pdf --profile my_brand
```

When no `--profile` is specified, the built-in defaults are used. If a `--config` file is provided instead, its values override the defaults directly without involving the profile system.
