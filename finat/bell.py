import numpy

import FIAT

from gem import Division, Indexed, Literal, ListTensor, Power, Product, Sum

from finat.fiat_elements import ScalarFiatElement
from finat.physically_mapped import PhysicallyMappedElement, Citations


class Bell(PhysicallyMappedElement, ScalarFiatElement):
    def __init__(self, cell, degree):
        if degree != 5:
            raise ValueError("Degree must be 3 for Bell element")
        if Citations is not None:
            Citations().register("Bell1969")
        super().__init__(FIAT.Bell(cell))

    def basis_transformation(self, coordinate_mapping):
        # Jacobians at edge midpoints
        J = coordinate_mapping.jacobian_at([1/3, 1/3])

        rns = coordinate_mapping.reference_normals()

        pts = coordinate_mapping.physical_tangents()

        pel = coordinate_mapping.physical_edge_lengths()

        V = numpy.zeros((21, 18), dtype=object)

        for multiindex in numpy.ndindex(V.shape):
            V[multiindex] = Literal(V[multiindex])

        for v in range(3):
            s = 6*v
            V[s, s] = Literal(1)
            for i in range(2):
                for j in range(2):
                    V[s+1+i, s+1+j] = Indexed(J, (j, i))
            V[s+3, s+3] = Power(Indexed(J, (0, 0)), Literal(2))
            V[s+3, s+4] = Product(Literal(2),
                                  Product(Indexed(J, (0, 0)),
                                          Indexed(J, (1, 0))))
            V[s+3, s+5] = Power(Indexed(J, (1, 0)), Literal(2))
            V[s+4, s+3] = Product(Indexed(J, (0, 0)),
                                  Indexed(J, (0, 1)))
            V[s+4, s+4] = Sum(Product(Indexed(J, (0, 0)),
                                      Indexed(J, (1, 1))),
                              Product(Indexed(J, (1, 0)),
                                      Indexed(J, (0, 1))))
            V[s+4, s+5] = Product(Indexed(J, (1, 0)),
                                  Indexed(J, (1, 1)))
            V[s+5, s+3] = Power(Indexed(J, (0, 1)), Literal(2))
            V[s+5, s+4] = Product(Literal(2),
                                  Product(Indexed(J, (0, 1)),
                                          Indexed(J, (1, 1))))
            V[s+5, s+5] = Power(Indexed(J, (1, 1)), Literal(2))

        for e in range(3):
            v0id, v1id = [i for i in range(3) if i != e]

            # nhat . J^{-T} . t
            foo = Sum(Product(Indexed(rns, (e, 0)),
                              Sum(Product(Indexed(J, (0, 0)),
                                          Indexed(pts, (e, 0))),
                                  Product(Indexed(J, (1, 0)),
                                          Indexed(pts, (e, 1))))),
                      Product(Indexed(rns, (e, 1)),
                              Sum(Product(Indexed(J, (0, 1)),
                                          Indexed(pts, (e, 0))),
                                  Product(Indexed(J, (1, 1)),
                                          Indexed(pts, (e, 1))))))

            # vertex points
            V[18+e, 6*v0id] = Division(
                Product(Literal(-1), foo),
                Product(Literal(21), Indexed(pel, (e,))))
            V[18+e, 6*v1id] = Division(
                foo,
                Product(Literal(21), Indexed(pel, (e,))))

            # vertex derivatives
            for i in (0, 1):
                V[18+e, 6*v0id+1+i] = Division(
                    Product(Literal(-1),
                            Product(foo,
                                    Indexed(pts, (e, i)))),
                    Literal(42))
                V[18+e, 6*v1id+1+i] = V[18+e, 6*v0id+1+i]

            # second derivatives
            tau = [Power(Indexed(pts, (e, 0)), Literal(2)),
                   Product(Literal(2),
                           Product(Indexed(pts, (e, 0)),
                                   Indexed(pts, (e, 1)))),
                   Power(Indexed(pts, (e, 1)), Literal(2))]

            for i in (0, 1, 2):
                V[18+e, 6*v0id+3+i] = Division(
                    Product(Literal(-1),
                            Product(Indexed(pel, (e,)),
                                    Product(foo, tau[i]))),
                    Literal(252))
                V[18+e, 6*v1id+3+i] = Division(
                    Product(Indexed(pel, (e,)),
                            Product(foo, tau[i])),
                    Literal(252))

        h = coordinate_mapping.cell_size()

        for v in range(3):
            for k in range(2):
                for i in range(21):
                    V[i, 6*v+1+k] = Division(V[i, 6*v+1+k],
                                             Indexed(h, (v,)))
            for k in range(3):
                for i in range(21):
                    V[i, 6*v+3+k] = Division(V[i, 6*v+3+k],
                                             Power(Indexed(h, (v,)),
                                                   Literal(2)))

        return ListTensor(V.T)

    # This wipes out the edge dofs.  FIAT gives a 21 DOF element
    # because we need some extra functions to help with transforming
    # under the edge constraint.  However, we only have an 18 DOF
    # element.
    def entity_dofs(self):
        return {0: {0: range(6),
                    1: range(6, 12),
                    2: range(12, 18)},
                1: {0: [], 1: [], 2: []},
                2: {0: []}}

    @property
    def index_shape(self):
        return (18,)

    def space_dimension(self):
        return 18
