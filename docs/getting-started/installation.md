# Installation

## conda-forge (recommended)

Installs obsidian-export with pandoc included automatically. You must separately install [tectonic](https://tectonic-typesetting.github.io/) >= 0.15 and [librsvg](https://wiki.gnome.org/Projects/LibRsvg) (not yet available on all platforms via conda-forge). Run `obsidian-export doctor` to check.

```bash
conda install -c conda-forge obsidian-export
```

Or with [pixi](https://pixi.sh/):

```bash
pixi global install obsidian-export
```

!!! note
    The conda-forge package is pending review. Until it's accepted, install from source using pixi:

    ```bash
    git clone https://github.com/neuralsignal/obsidian-export.git
    cd obsidian-export
    pixi install
    pixi run obsidian-export --help
    ```

## pip

```bash
pip install obsidian-export
```

With pip, you must separately install [pandoc](https://pandoc.org/) >= 3.5, [tectonic](https://tectonic-typesetting.github.io/) >= 0.15, and [librsvg](https://wiki.gnome.org/Projects/LibRsvg). Run `obsidian-export doctor` to check.

## Mermaid Support (optional)

For Mermaid diagram rendering, install [Node.js](https://nodejs.org/) >= 20 and [mermaid-cli](https://github.com/mermaid-js/mermaid-cli):

```bash
npm install -g @mermaid-js/mermaid-cli
```
