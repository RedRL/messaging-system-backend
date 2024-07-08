# Messaging System Backend

This repository contains the backend of a scalable messaging system using AWS services. It features AWS Lambda for function execution, DynamoDB for storage, and SQS for message queuing. Supports user registration, messaging, group chats, and blocking. Managed via CloudFormation, designed for efficient performance at scale.

## Table of Contents

- [Architecture](#architecture)
- [Setup](#setup)
- [API Endpoints](#api-endpoints)
  - [Register User](#register-user)
  - [Send Message](#send-message)
  - [Process User Message](#process-user-message)
  - [Block User](#block-user)
  - [Create Group](#create-group)
  - [Add User to Group](#add-user-to-group)
  - [Remove User from Group](#remove-user-from-group)
  - [Send Group Message](#send-group-message)
  - [Process Group Message](#process-group-message)
  - [Get New Messages](#get-new-messages)
  - [Get All Messages](#get-all-messages)

## Architecture

The backend system leverages the following AWS services:

- **AWS Lambda**: Handles the core business logic.
- **DynamoDB**: Stores user data, messages, groups, and blocks.
- **SQS**: Manages message queues for reliable processing.

## Setup

1. Deploy the CloudFormation stack:
    ```bash
    python deploy.py
    ```

## API Endpoints

### Register User

- **Endpoint**: `/register`
- **Method**: POST
- **Response Body**:
    ```json
    {
      "user_id": "1371c77f-62ed-43bb-86a3-ac3e56899c33"
    }
    ```

### Send Message

- **Endpoint**: `/send-message`
- **Method**: POST
- **Request Body**:
    ```json
    {
      "sender_id": "user123",
      "receiver_id": "user456",
      "message": "Hello!"
    }
    ```

### Process User Message

- **Endpoint**: Triggered by SQS Queue
- **Method**: N/A (handled internally)
- **Request Body**: N/A

### Block User

- **Endpoint**: `/block-user`
- **Method**: POST
- **Request Body**:
    ```json
    {
      "user_id": "user123",
      "blocked_user_id": "user456"
    }
    ```

### Create Group

- **Endpoint**: `/create-group`
- **Method**: POST
- **Request Body**:
    ```json
    {
      "group_name": "Group Name",
      "creator_id": "user123",
      "members": ["user123", "user456"]
    }
    ```

### Add User to Group

- **Endpoint**: `/add-user-to-group`
- **Method**: POST
- **Request Body**:
    ```json
    {
      "group_id": "group789",
      "user_id": "user456"
    }
    ```

### Remove User from Group

- **Endpoint**: `/remove-user-from-group`
- **Method**: POST
- **Request Body**:
    ```json
    {
      "group_id": "group789",
      "user_id": "user456"
    }
    ```

### Send Group Message

- **Endpoint**: `/send-group-message`
- **Method**: POST
- **Request Body**:
    ```json
    {
      "sender_id": "user123",
      "group_id": "group789",
      "message": "Hello group!"
    }
    ```

### Process Group Message

- **Endpoint**: Triggered by SQS Queue
- **Method**: N/A (handled internally)
- **Request Body**: N/A

### Get New Messages

- **Endpoint**: `/get-new-messages`
- **Method**: GET
- **Query Parameters**: `user_id`
- **Example Request**:
    ```
    /get-new-messages?user_id=user123
    ```

### Get All Messages

- **Endpoint**: `/get-all-messages`
- **Method**: GET
- **Query Parameters**: `user_id`
- **Example Request**:
    ```
    /get-all-messages?user_id=user123
    ```
