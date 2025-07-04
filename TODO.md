# To-Do

## 🔥 Next Up (Priority)

* [ ] **Réinjecter le rendu HTML dans les équipes** `(Due: Tomorrow)`
*   [ ] **Integrate Advanced Testing Libraries**
    *   [ ] Add `Faker` to `pyproject.toml` for generating realistic test data.
    *   [ ] Add `pytest-mock` to `pyproject.toml` for easier mocking in tests.
    *   [ ] Add `pendulum` to `pyproject.toml` for better date/time handling and time-freezing in tests.
    *   [ ] Run `uv sync` to install the new dependencies.
    *   [ ] Create a sample test in `tests/` demonstrating the usage of all three libraries.
    *   [ ] Update the `1_DEVELOPMENT_GUIDE.md` to include a section on these new testing standards.

*   [ ] **Set up and execute CrewAI within a container environment.**
    *   [ ] Install Docker on the host machine.
    *   [ ] Pull the official CrewAI container image from the Docker registry.
    *   [ ] Create a Dockerfile to customize the CrewAI environment if needed.
    *   [ ] Build the Docker image using the Dockerfile.
    *   [ ] Run the CrewAI container with the necessary configurations and environment variables.
    *   [ ] Verify the CrewAI execution and troubleshoot any issues that arise.


---

## 📋 Backlog (Future Tasks)

*   [ ] **Connect n8n to retrieve data initiated by CrewAI.**
*   [ ] **Connect n8n to initiate CrewAI integration.**
*   [ ] **Créer des agents pour le suivi technologique**
    *   [ ] Implement Nutanix AOS `(Due: 14 Jul)`
    *   [ ] Beta Netbackup `(Due: 15 Jul)`
    *   [ ] Implement Commvault B&R `(Due: 19 Jul)`
    *   [ ] PowerScale (Dell) `(Due: 28 Jul)`
    *   [ ] Eyeglass (Superna) `(Due: 2 Aug)`
    *   [ ] Suivi Tomcat `(Due: 13 Sep)`
    *   [ ] Implement Brocade FOS `(Due: 27 Sep)`
    *   [ ] Consul (HashiCorp)
    *   [ ] Implement Cisco UCS
    *   [ ] Implement Pure FlashArray
    -   [ ] Packer (HashiCorp)
    -   [ ] Suivi Nomad
    -   [ ] Terraform (HashiCorp)
* [ ] **Add Free APIs to the project**
  * [ ] Research and identify potential free APIs that align with the project's goals.
  * [ ] Evaluate the documentation and usage limits of the selected APIs.
  * [ ] Create a plan for integrating the chosen APIs into the project.
  * [ ] Write the necessary code to connect to and fetch data from the APIs.
  * [ ] Test the API integrations to ensure they function correctly within the project.
  * [ ] Document the API usage and any configuration steps for future reference.
