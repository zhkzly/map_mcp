# How to use?

```text
    1:git clone https://github.com/zhkzly/map_mcp.git
    2:uv sync

```

# how to use uv?
```text
    download:https://docs.astral.sh/uv/getting-started/installation/

    this can be used as pip

    添加新的依赖库
    pip install numpy  -> uv add numpy(or uv pip install numpy，不建议使用这种，因为他不会将库加入到依赖管理文件中，也就是 uv.lock)

    全部使用 uv add

    卸载某个库：uv remove numpy

    同步依赖：uv sync

    初始化一个新的项目  uv init --python=3.12.3 ,还有其他的配置选项，默认即可

    想要删掉当前的环境，直接remove .venv，和配置文件就行了

```