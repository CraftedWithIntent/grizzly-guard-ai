"""Tests for Grizzly Docker & Deployment (M1.8)."""

import os


def test_deployment_files_exist() -> None:
    """Test all deployment artifacts exist."""
    assert os.path.exists("Dockerfile")
    assert os.path.exists("docker-compose.yml")
    assert os.path.exists("deploy/k8s/deployment.yaml")
    assert os.path.exists(".github/workflows/publish.yml")


def test_dockerfile_multi_stage() -> None:
    """Test Dockerfile uses multi-stage build."""
    dockerfile = open("Dockerfile").read()
    assert "FROM python:3.11-slim as builder" in dockerfile
    assert "EXPOSE 8081" in dockerfile
    assert "HEALTHCHECK" in dockerfile


def test_docker_compose_valid() -> None:
    """Test docker-compose.yml structure."""
    compose = open("docker-compose.yml").read()
    assert "grizzly-proxy" in compose
    assert "services:" in compose


def test_k8s_deployment_valid() -> None:
    """Test Kubernetes deployment structure."""
    k8s = open("deploy/k8s/deployment.yaml").read()
    assert "kind: Deployment" in k8s
    assert "kind: Service" in k8s
    assert "grizzly-proxy" in k8s


def test_publish_workflow_valid() -> None:
    """Test publish workflow structure."""
    workflow = open(".github/workflows/publish.yml").read()
    assert "Publish" in workflow
    assert "pypi" in workflow.lower()
