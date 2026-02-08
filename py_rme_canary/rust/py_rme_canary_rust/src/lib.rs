use pyo3::prelude::*;

#[derive(Debug, Clone, FromPyObject)]
struct SpawnAreaPayload {
    x: i64,
    y: i64,
    z: i64,
    radius: i64,
    entries: Vec<(String, i64, i64)>,
}

fn compute_spawn_entry_names(payload: &[SpawnAreaPayload], x: i64, y: i64, z: i64) -> Vec<String> {
    let mut names: Vec<String> = Vec::new();

    for area in payload {
        if area.z != z {
            continue;
        }
        let dx = x - area.x;
        let dy = y - area.y;
        let radius = area.radius.max(0);
        if dx.abs().max(dy.abs()) > radius {
            continue;
        }

        for (name, entry_dx, entry_dy) in &area.entries {
            if *entry_dx == dx && *entry_dy == dy {
                names.push(name.clone());
            }
        }
        if !names.is_empty() {
            break;
        }
    }

    names
}

#[pyfunction]
fn spawn_entry_names_at_cursor(payload: Vec<SpawnAreaPayload>, x: i64, y: i64, z: i64) -> Vec<String> {
    compute_spawn_entry_names(&payload, x, y, z)
}

#[pymodule]
fn py_rme_canary_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(spawn_entry_names_at_cursor, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{compute_spawn_entry_names, SpawnAreaPayload};

    #[test]
    fn returns_names_at_cursor() {
        let payload = vec![SpawnAreaPayload {
            x: 100,
            y: 200,
            z: 7,
            radius: 4,
            entries: vec![
                ("Dragon".to_string(), 0, 0),
                ("Demon".to_string(), 1, 0),
                ("Warlock".to_string(), 0, 1),
            ],
        }];
        let names = compute_spawn_entry_names(&payload, 100, 200, 7);
        assert_eq!(names, vec!["Dragon".to_string()]);
    }

    #[test]
    fn respects_floor_and_radius() {
        let payload = vec![
            SpawnAreaPayload {
                x: 100,
                y: 200,
                z: 6,
                radius: 8,
                entries: vec![("WrongFloor".to_string(), 0, 0)],
            },
            SpawnAreaPayload {
                x: 100,
                y: 200,
                z: 7,
                radius: 1,
                entries: vec![("TooFar".to_string(), 0, 0)],
            },
        ];
        let names = compute_spawn_entry_names(&payload, 103, 203, 7);
        assert!(names.is_empty());
    }
}
