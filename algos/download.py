import os
from huggingface_hub import snapshot_download

def download_fin_retriever():
    repo_id = "valuesimplex-ai-lab/fin-retriever-base"

    # 相对路径：项目根目录下 models/
    target_dir = os.path.join(
        ".", "models", "valuesimplex-ai-lab", "fin-retriever-base"
    )

    print("====================================")
    print("开始下载模型：", repo_id)
    print("下载位置（相对路径）：", target_dir)
    print("====================================")

    snapshot_download(
        repo_id=repo_id,
        local_dir=target_dir,
        local_dir_use_symlinks=False,  # Windows 必须关
    )

    print("\n✅ 模型下载完成！")
    print("本地路径：", target_dir)


if __name__ == "__main__":
    download_fin_retriever()
