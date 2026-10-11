# 油橄榄双分支权重目录

本目录只接受使用油橄榄标签训练的 CNN+Transformer 双分支权重。`kozodoi/Kaggle_Leaf_Disease_Classification` 的木薯叶病害权重不能直接放入这里用于油橄榄诊断；它仅作为局部纹理与全局上下文融合的结构参考。

完成油橄榄数据训练并实现与当前页面相同的推理接口后，可放入 `best.pt` 或 `model.pt`，或通过 `OLIVE_HYBRID_WEIGHTS` 指向权重。当前版本会显示待训练状态，避免把不匹配的分类权重当成油橄榄模型运行。

也可以使用后端的 `train_dual_branch.py` 训练本软件约定的检查点：

```powershell
cd backend
python train_dual_branch.py C:\path\to\olive-imagefolder --output models\pest_hybrid\best.pt
```

检查点必须包含 `classes` 和 `state_dict`。这样可以防止误加载木薯项目的默认权重。
