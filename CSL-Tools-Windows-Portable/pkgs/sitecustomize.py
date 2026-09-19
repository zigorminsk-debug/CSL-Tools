import sys, os
# Auto-launch CSL-Tools if this is the main executable
# Prevent recursion
if not os.environ.get('CSL_TOOLS_AUTO'):
    os.environ['CSL_TOOLS_AUTO'] = '1'
    try:
        # Find main.py in parent directories
        exe_dir = os.path.dirname(sys.executable)
        # exe_dir is .../Python, parent is portable root
        root = os.path.dirname(exe_dir)
        # Also check exe_dir itself
        for base in [root, exe_dir, os.getcwd()]:
            main_path = os.path.join(base, 'main.py')
            if os.path.exists(main_path):
                if base not in sys.path:
                    sys.path.insert(0, base)
                # Launch
                import main
                main.main()
                sys.exit(0)
        # If not found, try launch.pyw
        launch_path = os.path.join(root, 'CSL-Tools.launch.pyw')
        if os.path.exists(launch_path):
            import runpy
            runpy.run_path(launch_path)
            sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        # Write error to file for debugging
        try:
            with open(os.path.join(os.path.expanduser('~'), 'CSL-Tools-error.log'), 'w', encoding='utf-8') as f:
                f.write(f"sitecustomize error: {e}\n")
                traceback.print_exc(file=f)
        except:
            pass
        traceback.print_exc()
