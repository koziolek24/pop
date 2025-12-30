use std::{collections::VecDeque, io::stdin, str::FromStr};

use rand::{
    Rng,
    distr::Uniform,
    random_range,
    seq::{IndexedRandom, SliceRandom},
};
use rayon::iter::{IndexedParallelIterator, IntoParallelIterator, ParallelIterator};

#[derive(Clone, Debug)]
struct Solution {
    working_groups: Vec<usize>,
    tasks: Vec<usize>,
}

impl Solution {
    fn score(&self, context: &Problem) -> usize {
        let mut queues = vec![VecDeque::<usize>::new(); context.group_count];
        let mut queues_times = vec![0; context.group_count];

        let mut tasks_finish_times = vec![0; context.task_count];
        let mut tasks_countdowns = context
            .tasks
            .iter()
            .map(|t| t.waits_for.len() as isize)
            .collect::<Vec<_>>();
        let mut task_precedesors_worst_time = vec![0; context.task_count];

        let mut runnable_tasks = VecDeque::new();

        self.working_groups
            .iter()
            .zip(self.tasks.iter())
            .for_each(|(&group, &task)| {
                queues[group].push_back(task);
            });

        queues.iter().enumerate().for_each(|(idx, q)| {
            if let Some(&f) = q.front().filter(|&&f| tasks_countdowns[f] == 0) {
                runnable_tasks.push_back((idx, f));
                tasks_countdowns[f] = -1;
            }
        });

        // println!("\n----------\n");

        // dbg!(&queues);
        // dbg!(&runnable_tasks);
        // dbg!(&tasks_countdowns);

        while let Some((queue_idx, running_task)) = runnable_tasks.pop_front() {
            // dbg!(&queues);
            // dbg!(&runnable_tasks);
            // dbg!(queue_idx, running_task);

            let queue = &mut queues[queue_idx];
            assert!(*queue.front().unwrap() == running_task);
            queue.pop_front();

            queues_times[queue_idx] = queues_times[queue_idx]
                .max(task_precedesors_worst_time[running_task])
                + context.tasks[running_task].working_time;

            tasks_finish_times[running_task] = queues_times[queue_idx];

            for &waiting_task in context.tasks[running_task].frees.iter() {
                tasks_countdowns[waiting_task] -= 1;
                task_precedesors_worst_time[waiting_task] =
                    task_precedesors_worst_time[waiting_task].max(tasks_finish_times[running_task]);
            }

            for (idx, q) in queues.iter().enumerate() {
                if q.front().filter(|&&t| tasks_countdowns[t] == 0).is_some() {
                    runnable_tasks.push_back((idx, *q.front().unwrap()));
                    tasks_countdowns[*q.front().unwrap()] = -1;
                }
            }
        }

        if queues.iter().all(VecDeque::is_empty) {
            tasks_finish_times.into_iter().max().unwrap_or_default()
        } else {
            usize::MAX
        }
    }

    fn new_random(context: &Problem) -> Self {
        let mut rng = rand::rng();

        let mut tasks_countdowns = context
            .tasks
            .iter()
            .map(|t| t.waits_for.len() as isize)
            .collect::<Vec<_>>();

        let mut free_tasks = context
            .tasks
            .iter()
            .enumerate()
            .filter(|(_, t)| t.waits_for.len() == 0)
            .map(|(idx, _)| idx)
            .collect::<Vec<_>>();

        let mut tasks = Vec::new();
        let mut working_groups = Vec::new();

        while !free_tasks.is_empty() {
            let idx = rng.random_range(0..free_tasks.len());
            let task = free_tasks.swap_remove(idx);
            tasks.push(task);
            working_groups.push(0);

            for &waiting_task in &context.tasks[task].frees {
                tasks_countdowns[waiting_task] -= 1;
                if tasks_countdowns[waiting_task] == 0 {
                    free_tasks.push(waiting_task);
                }
            }
        }

        assert!(tasks.len() == context.task_count);

        // let mut tasks = (0..context.task_count).collect::<Vec<_>>();
        // tasks.shuffle(&mut rng);
        //
        // let working_groups = std::iter::repeat_with(|| rng.random_range(0..context.group_count))
        //     .take(tasks.len())
        //     .collect::<Vec<_>>();

        Self {
            tasks,
            working_groups,
        }
    }

    fn mutate(&self, context: &Problem, mutation_chance: f64) -> Self {
        let mut mutated = self.clone();
        let mut rng = rand::rng();

        if rng.random_bool(mutation_chance) {
            if rng.random_bool(0.50) {
                // mutowanie permutacji zadań
                let index_1 = rng.random_range(0..mutated.tasks.len());
                let index_2 = rng.random_range(0..mutated.tasks.len());

                mutated.tasks.swap(index_1, index_2);
            } else {
                // mutowanie przydziału zadań
                let index = rng.random_range(0..mutated.tasks.len());
                let group = rng.random_range(0..context.group_count);

                mutated.working_groups[index] = group;
            }
        }

        mutated
    }
}

#[derive(Default, Clone)]
struct Task {
    waits_for: Vec<usize>,
    frees: Vec<usize>,
    working_time: usize,
}

#[derive(Clone)]
struct Problem {
    group_count: usize,
    task_count: usize,
    tasks: Vec<Task>,
}

impl Problem {
    fn new(
        group_count: usize,
        task_count: usize,
        tasks_precedence_matrix: Vec<Vec<i8>>,
        task_times: Vec<usize>,
    ) -> Result<Self, String> {
        if !(task_count != 0
            && task_count == tasks_precedence_matrix.len()
            && task_count == tasks_precedence_matrix[0].len())
            || task_count == 0
            || group_count == 0
            || task_count != task_times.len()
        {
            return Err("Invalid input".to_string());
        }

        let mut tasks = vec![Task::default(); task_count];
        for ((&time, task), relations) in task_times
            .iter()
            .zip(tasks.iter_mut())
            .zip(tasks_precedence_matrix.iter())
        {
            task.working_time = time;
            for (other_task, &priority) in relations.iter().enumerate() {
                if priority == -1 {
                    task.waits_for.push(other_task);
                } else if priority == 1 {
                    task.frees.push(other_task);
                }
            }
        }

        Ok(Self {
            group_count,
            task_count,
            tasks,
        })
    }
}

struct Config {
    generation_count: usize,
    population_size: usize,
    mutation_chance: f64,
    sample_size: usize,
}

fn evolution(problem: &Problem, config: Config) -> Solution {
    let mut population = std::iter::repeat_with(|| Solution::new_random(&problem))
        .take(config.population_size)
        .collect::<Vec<_>>();

    let mut rng = rand::rng();

    for generation in 0..config.generation_count {
        // println!("Generation: {generation}");
        // println!(
        //     "Best score: {}",
        //     population.iter().map(|s| s.score(&problem)).min().unwrap()
        // );

        population.shuffle(&mut rng);
        population = population
            .into_par_iter()
            .chunks(config.sample_size)
            .map(|pops| {
                pops.into_iter()
                    .min_by_key(|s| s.score(&problem))
                    .unwrap()
                    .clone()
            })
            .collect::<Vec<_>>();

        while population.len() != config.population_size {
            let new = population
                .choose(&mut rng)
                .unwrap()
                .mutate(&problem, config.mutation_chance);
            population.push(new);
        }
    }

    return population
        .into_iter()
        .min_by_key(|s| s.score(&problem))
        .unwrap();
}

fn main() -> Result<(), String> {
    use scan_fmt::scan_fmt;
    use scan_fmt::scanln_fmt;

    // read task_count and group_count
    let (task_count, group_count): (usize, usize) = scanln_fmt!("{} {}", usize, usize).unwrap();

    // read task_times
    let mut task_times = Vec::with_capacity(task_count);
    for _ in 0..task_count {
        let t: usize = scanln_fmt!("{}", usize).unwrap();
        task_times.push(t);
    }

    // read task_count x task_count matrix
    let mut matrix = vec![vec![0i8; task_count]; task_count];
    for i in 0..task_count {
        let mut buf = String::new();
        stdin().read_line(&mut buf).unwrap();
        matrix[i] = buf
            .split_whitespace()
            .map(str::parse::<i8>)
            .map(Result::unwrap)
            .collect::<Vec<_>>();
        assert!(matrix[i].len() == task_count);
    }

    // ---- sanity check ----
    // println!("task_count = {}", task_count);
    // println!("group_count = {}", group_count);
    // println!("task_times = {:?}", task_times);
    // println!("matrix[0] = {:?}", matrix[0]);

    let cfg = Config {
        generation_count: 1000,
        population_size: 100,
        mutation_chance: 1.0,
        sample_size: 10,
    };

    let p = Problem::new(group_count, task_count, matrix, task_times).unwrap();

    // let s = Solution::new_random(&p);
    // dbg!(&s);
    // dbg!(&s.score(&p));

    // return Ok(());

    let best = evolution(&p, cfg);

    println!("{}", best.score(&p));

    Ok(())
}
