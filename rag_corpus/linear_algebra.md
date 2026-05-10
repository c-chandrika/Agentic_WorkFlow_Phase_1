# Linear algebra — undergraduate reference (RAG corpus)

This note is for **linear algebra** topics: vectors, matrices, eigenvalues, and linear transformations.

## Vectors and subspaces

A **vector space** over \(\mathbb{R}\) is closed under addition and scalar multiplication. A **subspace** must contain \(0\), be closed under addition, and under scaling. The **span** of vectors \(\{v_1,\ldots,v_k\}\) is the set of all linear combinations \(\sum_i c_i v_i\).

## Linear independence and basis

Vectors are **linearly independent** if \(\sum_i c_i v_i = 0\) implies all \(c_i=0\). A **basis** is an independent spanning set; the **dimension** of a subspace is the number of vectors in any basis. The **column space** (range) of a matrix \(A\) is the span of its columns; the **null space** is \(\{x : Ax=0\}\). Rank–nullity: \(\mathrm{rank}(A) + \dim(\mathrm{Nul}(A)) = n\) for \(A \in \mathbb{R}^{m \times n}\).

## Matrices as linear maps

Matrix multiplication represents composition of linear maps: \((AB)x = A(Bx)\). **Transpose** satisfies \((AB)^T = B^T A^T\). An **orthogonal matrix** \(Q\) satisfies \(Q^T Q = I\); it preserves lengths and angles.

## Systems \(Ax=b\)

**Consistency:** \(Ax=b\) has a solution iff \(b\) lies in the column space of \(A\). For square invertible \(A\), the unique solution is \(x=A^{-1}b\). **Gaussian elimination** reveals pivot columns, rank, and a parametric form of solutions when the system is underdetermined.

## Determinant and invertibility

For square \(A\), \(\det(A)\neq 0\) iff \(A\) is invertible. Determinant is multiplicative: \(\det(AB)=\det(A)\det(B)\). Geometrically, \(|\det(A)|\) scales volume in \(\mathbb{R}^n\).

## Eigenvalues and eigenvectors

A nonzero vector \(v\) is an **eigenvector** of \(A\) with **eigenvalue** \(\lambda\) if \(Av=\lambda v\). Eigenvalues are roots of the **characteristic polynomial** \(\det(A-\lambda I)=0\). **Diagonalization:** if \(A\) has \(n\) independent eigenvectors, then \(A=PDP^{-1}\) with \(D\) diagonal. **Symmetric** real matrices have real eigenvalues and an orthonormal basis of eigenvectors.

## Inner products and orthogonality

The standard inner product on \(\mathbb{R}^n\) is \(u \cdot v = u^T v\). Vectors are **orthogonal** if \(u \cdot v=0\). **Gram–Schmidt** turns an independent set into an orthonormal set spanning the same subspace.

## Positive definite matrices

A symmetric matrix \(A\) is **positive definite** if \(x^T A x > 0\) for all nonzero \(x\); equivalently all eigenvalues are positive. Such matrices appear in covariance matrices and quadratic forms.

Use these ideas when writing **linear algebra** MCQs at L2: distinguish span vs basis, rank vs determinant, and eigenvalue definitions vs “magic numbers” in examples.
