# Probability — undergraduate reference (RAG corpus)

This note is for **probability** topics: random variables, distributions, conditioning, and counting.

## Sample spaces and events

A **sample space** is the set of all possible outcomes of an experiment. An **event** is a subset of the sample space. The **complement** of event \(A\) is \(A^c\), containing all outcomes not in \(A\). For any finite sample space with equally likely outcomes, \(P(A) = |A| / |\Omega|\).

## Axioms and basic rules

Probabilities satisfy: \(P(A) \ge 0\), \(P(\Omega)=1\), and for disjoint events \(A_1,A_2,\ldots\), \(P(\bigcup_i A_i) = \sum_i P(A_i)\). From this: \(P(A^c)=1-P(A)\), and for any \(A,B\), \(P(A \cup B) = P(A)+P(B)-P(A \cap B)\).

## Conditional probability and independence

**Conditional probability:** \(P(A \mid B) = P(A \cap B)/P(B)\) when \(P(B)>0\). **Multiplication rule:** \(P(A \cap B) = P(B)\,P(A \mid B)\).

Random variables \(X\) and \(Y\) are **independent** if for all reasonable sets \(S,T\), \(P(X \in S, Y \in T) = P(X \in S)\,P(Y \in T)\). For discrete variables, independence implies the joint mass function factors: \(p_{X,Y}(x,y)=p_X(x)\,p_Y(y)\) for all \(x,y\). A common mistake is to confuse “uncorrelated” with “independent”; independence is stronger (except in special Gaussian cases).

## Bayes’ theorem

For a partition \(B_1,\ldots,B_n\) of the sample space with \(P(B_i)>0\),

\[
P(B_j \mid A) = \frac{P(A \mid B_j)\,P(B_j)}{\sum_i P(A \mid B_i)\,P(B_i)}.
\]

Here \(P(B_j)\) is the **prior**, \(P(A \mid B_j)\) the **likelihood**, and \(P(B_j \mid A)\) the **posterior**.

## Discrete distributions

**Bernoulli(\(p\)):** one trial, success probability \(p\). **Binomial(\(n,p\)):** number of successes in \(n\) independent Bernoulli trials; mean \(np\), variance \(np(1-p)\). **Geometric(\(p\)):** trials until first success; **Poisson(\(\lambda\)):** counts in fixed interval with rate \(\lambda\); mean and variance \(\lambda\).

## Continuous distributions

**Uniform(\(a,b\))** density \(1/(b-a)\) on \([a,b]\). **Exponential(\(\lambda\))** models waiting times with rate \(\lambda\); memoryless property. **Normal(\(\mu,\sigma^2\))** appears as a limit (CLT) and has symmetric bell-shaped density.

## Expectation and variance

For discrete \(X\), \(E[X]=\sum_x x\,P(X=x)\). **Linearity:** \(E[aX+bY+c]=aE[X]+bE[Y]+c\) even if \(X,Y\) are dependent. **Variance:** \(\mathrm{Var}(X)=E[(X-E[X])^2]=E[X^2]-(E[X])^2\). For independent \(X,Y\), \(\mathrm{Var}(X+Y)=\mathrm{Var}(X)+\mathrm{Var}(Y)\).

## Law of total probability and expectation

If \(B_i\) partition \(\Omega\), \(P(A)=\sum_i P(A \mid B_i)\,P(B_i)\). Similarly, **law of total expectation:** \(E[X]=\sum_i E[X \mid B_i]\,P(B_i)\) (discrete case; continuous analogs use integrals).

Use these ideas when writing **probability** MCQs at L2: stress correct use of independence, conditioning, and whether a story matches binomial vs geometric vs Poisson assumptions.
