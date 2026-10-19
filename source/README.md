# 当时执行器的来源快照

这些文件用于说明提示词、解析、重试和赛后补问的实际实现。它们保持当时的项目结构依赖，不是脱离原工程就能重跑所有在线模型的一键程序。

本仓库的离线核验入口是 tools/verify.py；文档与图像生成入口是 tools/build_docs.py 和 tools/build_visuals.py。核验不需要原工程、Lodestar 或模型账号。
