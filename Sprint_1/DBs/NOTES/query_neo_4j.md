| Task                    | Cypher Syntax                                  |
| :---------------------- | :--------------------------------------------- |
| **Create/Find Node**    | `MERGE (n:Label {key: 'val'})`                 |
| **Create Relationship** | `MERGE (a)-[:REL_TYPE]->(b)`                   |
| **Filter by Property**  | `MATCH (n) WHERE n.age > 20`                   |
| **Delete Relationship** | `MATCH (a)-[r:FOLLOWS]->(b) DELETE r`          |
| **Delete Node**         | `MATCH (n:User {name: 'Nik'}) DETACH DELETE n` |



