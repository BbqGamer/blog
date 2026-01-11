+++
title = 'MetaWeighting paper overview'
date = 2026-01-07T21:40:33+01:00
draft = false
math = true
+++
# The paper
In this blogpost we'll expore the paper: [*MetaWeighting: Learning to Weight
Tasks in Multi-Task Learning*](https://aclanthology.org/2022.findings-acl.271/)
authored by: *Yuren Mao, Zekai Wang, Weiwei Liu, Xuemin Lin and Pengtao Xie*,

The paper introduces a novel algorithm to dynamically adjust weights in Multi Task
Learning setting via learning-to-learn paradigm.

# Multi-Task learning
Multi-Task Learning (MTL) is a powerful concept in machine learning. It allows
to share weights of the model between multiple tasks, it forces the model to
learn a shared representation that can generalize better than if each task was
learned in isolation.

However in practice, MTL is not so straightforward. Tasks compete for the
model's limited capacity. Some tasks are noisy, some are easy, and some are
incredibly complex. If you treat them all equally, one task might dominate the
training process, causing the others to suffer. This is known as task
imbalance.

A common approach to mitigating this issue is task weighting, where the overall
loss is expressed as a weighted sum of task-specific losses:
$$
L =  w_1 \mathcal{L}_1 + w_2 \mathcal{L}_2 + \dots + w_T \mathcal{L}_T
$$ 

By adjusting the weights $w_t$, we can control how much influence each task has
during training. However, using fixed (static) weights introduces additional
hyperparameters that are difficult to tune and highly problem-dependent. Most
successful task weighting strategies (like [Uncertainty
Weighting](https://arxiv.org/abs/1705.07115) or
[GradNorm](https://arxiv.org/abs/1711.02257) are adaptive.

# Limitations of existing methods
Despite their success, most existing task weighting methods share a fundamental
limitation: they compute task weights solely based on training loss or training
gradients. In deep learning, a model can easily "memorize" the training data
(achieving low training loss) without actually learning the underlying patterns
needed for previously unseen data (generalization). Authors of the
MetaWeighting paper recognize existence of gap between training and generalization
loss, and argue that dynamic adjustment of the task weights should be guided by
the generalization loss.

# The MetaWeighting algorithm
## Support Query dataset split
Because it is impossible to actually calculate generlization loss, you have to
approximate it somehow, the authors were able to achieve that by splitting data
into two parts:
 - Support Set ($D_s$): Used to train the model parameters.
 - Query Set ($D_q$): Used to estimate generalization loss and update the
task weights.

## The training loop
The training process is formulated as a "loop within a loop" (Bi-level optimization).
### 1. The Inner Loop (Training the Model)
The model updates its parameters (θ)
to minimize the weighted loss on the support set. This is standard backpropagation.
### 2. The Outer Loop (Training the Task Weights)
The algorithm updates the task weights (w) to minimize the loss on a separate
validation set (referred to as the "Query" set). Most of the paper innovation
lies in the second loop. The authors treat task weighting not as a heuristic,
but as a parameter to be learned via meta-learning.
The outer loop consists of 3 stages:

#### A. Calculate the "Look-Ahead" Gradients ([Hypergradient descent](https://arxiv.org/abs/1703.04782)
The algorithm calculates a special gradient for the weights. It effectively
simulates one step of training and checks the result. The chain rule is used to 
connect the hyperparmeters (Task Weights) to Model Parameters and Query Loss.

#### B. Find the Common Direction (The Theorem)
Now the algorithm has a "wishlist" of weight changes from every task. Task 1
wants weights to change in direction $d_1$, Task 2 in the direction $d_2$ etc.
We would like to find a common descent direction $d_s$ that would benefit all
the tasks.

This optimization problem is solved using the [Frank–Wolfe algorithm](https://arxiv.org/abs/2503.08921), and works
by findin the closes vector to the origin that is inside the convex hull
created from the vectors $d_1, \dots d_n$. If the resulting vector is non-zero,
it guarantees a common descent direction: taking a sufficiently small step
along it will not worsen any task’s query loss.

#### C. Update the task weights
Finally, the task weights are updated using this common direction, multiplied by
some learning rate.

After that we go back to the Inner Loop (training the model) with the new weights
and repeat the cycle until algorithm converges.

# What are benefits of MetaWeighting algorithm
1. Optimization Aligned with Generalization
Rather than relying on training loss as a proxy, MetaWeighting optimizes query
loss, which the authors theoretically and empirically show to be a tighter
estimator of generalization loss than training loss.

2. No Hand-Designed Heuristics
Many weighting methods require careful tuning or rely on assumptions about task
difficulty. MetaWeighting learns the weights automatically from the data
pattern itself.

3. Theoretical Backing
The paper provides a theoretical analysis showing that the "Query Loss" (loss
on the held-out split) is a mathematically tighter bound for true
generalization error than Training Loss is.

# Experimental Results
The authors tested MetaWeighting on standard multi-task benchmarks like
Sentiment Analysis (classifying reviews across different domains) and Topic
Classification (classifying news articles).

MetaWeighting consistently outperformed standard baselines (like
Single-Task Learning and Uniform Weighting) and sophisticated state-of-the-art
methods (like GradNorm and [MGDA](https://www.semanticscholar.org/paper/Multiple-gradient-descent-algorithm-(MGDA)-for-D%C3%A9sid%C3%A9ri/b7ef79008d87bce38144b6f1a06e36870e1c2449)).

Interestingly, the weights learned by MetaWeighting didn't follow a simple
pattern. They fluctuated and adapted in complex ways that human-designed
heuristics didn't capture, suggesting the method was finding non-obvious
balances between tasks.

# Summary
MetaWeighting represents a shift in how we think about Multi-Task Learning.
Instead of asking "which task is learning the slowest?" (training loss), it
asks "which task is failing to generalize?" (query loss). By aligning the
training incentive with the ultimate goal of generalization, it allows models
to juggle competing tasks more effectively.

# Bibliography
- MetaWeighting: Learning to Weight Tasks in Multi-Task Learning - Yuren Mao, Zekai Wang, Weiwei Liu, Xuemin Lin and Pengtao Xie
- Multi-Task Learning Using Uncertainty to Weigh Losses for Scene Geometry and
  Semantics - Alex Kendall, Yarin Gal, Roberto Cipolla
- GradNorm: Gradient Normalization for Adaptive Loss Balancing in Deep
  Multitask Networks - Zhao Chen, Vijay Badrinarayanan, Chen-Yu Lee, Andrew
Rabinovich
- Online Learning Rate Adaptation with Hypergradient Descent - Atilim Gunes
  Baydin, Robert Cornish, David Martinez Rubio, Mark Schmidt, Frank Wood
- Revisiting Frank-Wolfe for Structured Nonconvex Optimization - Hoomaan
  Maskan, Yikun Hou, Suvrit Sra, Alp Yurtsever
- Multiple-gradient descent algorithm (MGDA) for multiobjective optimization -
  J. Désidéri

