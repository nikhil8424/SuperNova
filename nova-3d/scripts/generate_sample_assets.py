"""
Generate synthetic sample assets for NOVA 3D:
1. Multi-part structured GLB model (Engine Assembly with named components and hierarchy)
2. Synthetic camera orbit video (MP4) for frame extraction and CV pipeline verification
"""
import os
import math
import numpy as np
import cv2
import trimesh

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "samples"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_sample_engine_glb():
    glb_path = os.path.join(OUTPUT_DIR, "engine_assembly.glb")
    scene = trimesh.Scene()
    
    # 1. Engine Block (Base)
    block = trimesh.creation.box(extents=[2.0, 1.5, 1.2])
    block.visual.face_colors = [70, 75, 85, 255] # Dark slate
    block.metadata = {"name": "EngineBlock", "category": "Housing", "material": "Cast Iron"}
    scene.add_geometry(block, node_name="EngineBlock", geom_name="EngineBlock")
    
    # 2. Cylinder Head (Top)
    cyl_head = trimesh.creation.box(extents=[1.9, 1.4, 0.4])
    cyl_head.apply_translation([0, 0, 0.8])
    cyl_head.visual.face_colors = [120, 130, 140, 255] # Silver
    cyl_head.metadata = {"name": "CylinderHead", "category": "TopAssembly", "parent": "EngineBlock"}
    scene.add_geometry(cyl_head, node_name="CylinderHead", geom_name="CylinderHead")
    
    # 3. Piston Assembly Left
    piston_l = trimesh.creation.cylinder(radius=0.25, height=0.6)
    piston_l.apply_translation([-0.5, 0, 0.3])
    piston_l.visual.face_colors = [0, 210, 255, 255] # Electric Cyan
    piston_l.metadata = {"name": "Piston_Left", "category": "InternalPiston", "parent": "EngineBlock"}
    scene.add_geometry(piston_l, node_name="Piston_Left", geom_name="Piston_Left")

    # 4. Piston Assembly Right
    piston_r = trimesh.creation.cylinder(radius=0.25, height=0.6)
    piston_r.apply_translation([0.5, 0, 0.3])
    piston_r.visual.face_colors = [0, 210, 255, 255] # Electric Cyan
    piston_r.metadata = {"name": "Piston_Right", "category": "InternalPiston", "parent": "EngineBlock"}
    scene.add_geometry(piston_r, node_name="Piston_Right", geom_name="Piston_Right")

    # 5. Crankshaft (Bottom)
    crankshaft = trimesh.creation.cylinder(radius=0.15, height=2.2)
    # Rotate horizontally along X axis
    rot = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
    crankshaft.apply_transform(rot)
    crankshaft.apply_translation([0, 0, -0.4])
    crankshaft.visual.face_colors = [180, 140, 60, 255] # Bronze / Brass
    crankshaft.metadata = {"name": "Crankshaft", "category": "Drivetrain", "parent": "EngineBlock"}
    scene.add_geometry(crankshaft, node_name="Crankshaft", geom_name="Crankshaft")

    # 6. Spark Plug Cluster
    plug = trimesh.creation.cone(radius=0.1, height=0.35)
    plug.apply_translation([0, 0, 1.1])
    plug.visual.face_colors = [160, 32, 240, 255] # Electric Violet
    plug.metadata = {"name": "SparkPlug", "category": "Ignition", "parent": "CylinderHead"}
    scene.add_geometry(plug, node_name="SparkPlug", geom_name="SparkPlug")

    # 7. Exhaust Manifold Flange
    flange = trimesh.creation.box(extents=[1.6, 0.2, 0.3])
    flange.apply_translation([0, 0.85, 0.2])
    flange.visual.face_colors = [220, 80, 50, 255] # Heat resistant orange
    flange.metadata = {"name": "ExhaustManifold", "category": "Exhaust", "parent": "EngineBlock"}
    scene.add_geometry(flange, node_name="ExhaustManifold", geom_name="ExhaustManifold")

    # Export to GLB
    data = trimesh.exchange.gltf.export_glb(scene)
    with open(glb_path, "wb") as f:
        f.write(data)
    print(f"Generated sample model: {glb_path} (bytes: {len(data)})")

def generate_sample_walkthrough_video():
    video_path = os.path.join(OUTPUT_DIR, "sample_walkthrough.mp4")
    width, height = 640, 480
    fps = 30
    duration_sec = 4
    total_frames = fps * duration_sec

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

    for i in range(total_frames):
        angle = 2 * math.pi * (i / total_frames)
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Dark tech background
        cv2.rectangle(frame, (0, 0), (width, height), (18, 18, 24), -1)

        # Draw grid
        for gx in range(0, width, 40):
            cv2.line(frame, (gx, 0), (gx, height), (30, 32, 42), 1)
        for gy in range(0, height, 40):
            cv2.line(frame, (0, gy), (width, gy), (30, 32, 42), 1)

        # 3D simulated rotating target
        cx = int(width / 2 + 120 * math.cos(angle))
        cy = int(height / 2 + 60 * math.sin(angle))
        radius = int(50 + 15 * math.sin(angle * 2))

        # Glowing circles & components
        cv2.circle(frame, (cx, cy), radius, (255, 200, 0), 2)
        cv2.circle(frame, (cx, cy), int(radius * 0.6), (200, 50, 160), -1)
        cv2.circle(frame, (int(width/2), int(height/2)), 80, (0, 230, 255), 2)

        # Text HUD
        cv2.putText(frame, "NOVA 3D CAPTURE RIG - ORBITAL TEST", (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 230, 255), 2)
        cv2.putText(frame, f"FRAME {i+1:04d} / {total_frames:04d} | ANGLE: {math.degrees(angle):.1f} DEG", 
                    (30, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (160, 160, 180), 1)

        out.write(frame)

    out.release()
    print(f"Generated sample video: {video_path}")

if __name__ == "__main__":
    generate_sample_engine_glb()
    generate_sample_walkthrough_video()
