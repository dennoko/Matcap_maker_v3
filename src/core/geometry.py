import numpy as np
import math

class GeometryEngine:
    @staticmethod
    def generate_sphere(radius=0.9, stacks=30, sectors=30, offset_x=0.0):
        """
        Generate Sphere with Position, Normal, UV, and Tangent.
        Format: [Pos(3), Normal(3), UV(2), Tangent(3)]
        Total stride: 11 floats
        """
        vertices = []
        indices = []
        
        for i in range(stacks + 1):
            lat = math.pi * i / stacks
            y = math.cos(lat)
            r_plane = math.sin(lat)
            for j in range(sectors + 1):
                lon = 2 * math.pi * j / sectors
                x = r_plane * math.cos(lon)
                z = r_plane * math.sin(lon)
                
                # Position
                px, py, pz = x*radius + offset_x, y*radius, z*radius
                
                # Normal (Normalized local pos)
                nx, ny, nz = x, y, z
                
                # UV
                u = j / sectors
                v = i / stacks
                
                # Tangent (Derivative of position with respect to U (longitude))
                # T = (-sin(lon), 0, cos(lon)) -> approx
                tx = -math.sin(lon)
                ty = 0.0
                tz = math.cos(lon)
                
                vertices.extend([px, py, pz, nx, ny, nz, u, v, tx, ty, tz])

        for i in range(stacks):
            for j in range(sectors):
                first = (i * (sectors + 1)) + j
                second = first + sectors + 1
                indices.extend([first, second, first + 1, second, second + 1, first + 1])
                
        return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint32)

    @staticmethod
    def generate_comparison_spheres():
        """
        Left Sphere (-0.6) for Matcap Generator.
        Right Sphere (+0.6) for Normal Map Preview.
        Radius 0.55.
        """
        # Left Sphere
        s1_verts, s1_inds = GeometryEngine.generate_sphere(radius=0.55, offset_x=-0.6)
        
        # Right Sphere
        s2_verts, s2_inds = GeometryEngine.generate_sphere(radius=0.55, offset_x=0.6)
        
        # Merge
        s2_inds_offset = s2_inds + (len(s1_verts) // 11)
        
        merged_verts = np.concatenate([s1_verts, s2_verts])
        merged_inds = np.concatenate([s1_inds, s2_inds_offset])
        
        return merged_verts, merged_inds
